#!/usr/bin/env python3
"""news-image-20261124 -- Tuesday 24 November 2026 world news front page.

Draws a 1024x1024 newspaper front page summing up the day's world news:
50 stories (1 hero + 49) across 7 regions, every story carrying its source,
a UTC timeline, a numbered world map, a DATE CHECK box naming stories that
did NOT happen today, and an ALSO TODAY strip.

Pure standard library (struct, zlib, base64, math, os, sys). No network, no
timestamps, no randomness: two runs write byte-identical PNGs.

The text is rendered from bitmap glyph tables embedded below. The tables
were produced at build time by rasterising the freely licensed DejaVu fonts
at 48 px and thresholding to 1 bit; the program itself only decodes them.
"""

import base64
import binascii
import math
import os
import struct
import sys
import zlib

# ---------------------------------------------------------------------------
# Embedded bitmap fonts (base85 of a packed binary table).
# Table format: header ">HHH" (font size px, ascent px, glyph count), then
# per glyph ">HBBBB" (codepoint, advance, width, height, top offset from the
# top of the em box) followed by ceil(width*height/8) bytes of 1-bit pixels,
# row-major, MSB first. A glyph's baseline sits `ascent` px below the em top.
# ---------------------------------------------------------------------------
FONT_REG_B85 = "05AY80BHaq4*&oF03j0vBMSfj|NsC0|NsC0|Nr;B?*IS*fB*mf03sF+4GMU9;pc~*9(Z}-=ZBsiczNOHhn^mIcmN|PA|na_1HgCy0Pq|D05}f-03HLt00)5Z00H1Q003|v002A(fB+8x-~a=_Z~_1S|NMXd|NkHV|NqDT|Nrm-;CKK4@E!mFJO_XP4*|dc1Ay=V0pL6U0C*1oAOHXVhyVZo;s5{t_<#TZ{s24&000gHzyJq;@BjheJOBWA4gdfi2Y>(v0pI`wz<2-v@EiaDJP!Z>03;t6EC>J?000;O02lxO7ytkm000;O0RP|z|M(C8_#glHKNuK37yx`20C*Sxco+b97yx`206rK1KbQa?{s0gEzytsA0RQ*^AN&9qegGIg02m$s7#{!_9{?C002m%X7(RR${D1%afB*PD|KJ1v000;O02lxO7ytkm000;O02lxO7ytkzE-57m1MmO?fCu~l1HcFWfCIn>!@vRH1HkYB-~+&T0N?@O902eD@DBj+0B{F@cmOy9z<2;00pK_Q4*>8y00)3@JOBg0cpd-%@H`#>0DL?S001BU4*&oM{09I40Q?7l`~Uz4f&YL21A+hG00Y7B@Bjh8@H_wk;P4&*0pNHCfB^731Hb_A9s%G0a1Q|R0C)$0cmQ|<z&rpv0pK10JOJ<>02}~34*(tj9}fT?00;ko4*&uGfDZrwKL7wGB_SmV06%~L0Dt%Z0RR2~0Du1g0DcF606qXf06qW!03QGV01p5F00+PT00ZCv008&^004Xd0018V000lb000m0000mC000la01pq3zz2te@B_!d`~%~_KLO+555V#81MqnG0Q`7-06#oF01x~h00aIHfB^mj-~c}X_y9k^egHr4AHaY75C8u@0ssCFfPel2;0O2s001Wq1q}*&-uJ!ld*1he04Ng+D+vMMcn<@>cpd}5@E!-i@E!-i_#Okmcpn4cd=G)}J_o?~9|7Pz2Y~n=0pL6bz<3V;@E!r+JOjXZ2Y>)66AUW}cmseu0pK10@DBj^2Y`47z&r!MJ_Fz$0pK11;2#0-9|7<m0pK11;2s0uJ_Eo!2f%m-fcOsp@E!r+JOhAu001f&78VHrFaQ9+00RI33;-Z75x~Ib!w-*)d=LM?5BvZRzyLo01OEU&{{iD39}GTlFgSp~Kmz~(3;+Ny006)M04pdT9uEKqfB*mw0000U0000y0001Z0002+0005t000BP000Mo000jF0015U002Ay004LZAOHXVzyJULfB*mf|NsB|01p5F03HAU06YKy0C)fZ0Pp|+0pI`t1Hb?P2Y>(o4*&oF9smFUJOBUycmMzZ@Bjb+EDs0_Cm$alA09qDJUDo8Z~!e44Fn$l|NsC0|L_1V4+aJ&`|rN{-~cZW5hn@&4*&;%2Y>^>0pJ1P0Pp~K06YLZ03HAj01p5MfCIn-zyaU@@Br`tcmO;AJOCa54*&;%2Y>^>0pJ1P0Pp~K0C)gA03HAy01p5MfCqpBzyJU+9~mVH0Dk}g|KI`t_yPa^0sJ3;_y^$l0q}ePd^`X?J^&9N00+;21LuGN_rL)A-~fH_03P@N4}1Uzz5oN?00HlS0QbNEd*A?l@Blt|03SX851#-B&wvBNzysm%0r2<%@IC?fAHnzs|M&s__y9ln00-~@05KmHBMJfd0RP|*|A0UK0RDIb0pI`!fB+r<0C)fa-~b1J03HAUcmM(500)2o9smG%00H0t2Y>(`004LZ0pI`!fB+r<0C)fa-~b1J03HAUcmM(500)2{|Nejf`Tzgt|NnphG9MQt2?PEBfBymh|AYVkhu}Ys06!1_KL7we002Ay0C)fZ_y7Um00+PT4}bt4004Xd0r&t1-~bPR06qW!_y7ao01towJ^%pt00ZCv55NFF008^|1MmP3zyLo00Du4f|Ns5}|NH;{@BlL(7$pe-{s15Uz(4=+KmYhX1N<NW`~U!a002G!06qW!J^%nd002G!0DJ%d`~U;^0srs;|G)wN-~s>e00Z~{0Q>*|egFVI0015U03QGV9{>O!0018V03HAUJ^%oIU;zAl1N?vg_<#T4KmWi3{r~_p9~vVH00H;_0R8{~e}DiV-~bQ!00+JR0q=kS^WXq@_y8V001pp<2ZP`N;P?RWJ^*|VfF1+j4*>WBz&-)s4}kCk;5-2M9soWMfDeQJ|NsC0|NsC0|NsB|00ZCv0Qdj^J^%m@fB*yF008&^06qW!4}btQ9~dMGKmYhY|M)-u_&@*nJ^%nd002G!06qW!J^%nd002G!06qW!KmGte|A0UL;6MNHJO}t70sH^}d;kD`002G!06qW!J^%n70015U06qW!J^%nd004eK0DNEp{Co%afB*1*|KLCWfCu~l05%^PB?$l@@Bn}Q0Du1gfB%4g0Kk3#0Db@fJ^%nd0018V01p5F4}bs%zyJf``~l<tfb;+G`~UoZ;C?^gAD`d{&)@;~-~jpX0DSlW9((`~J^%-w00Yl}1LME}@$dlnd;s`90Q?WY`~&~|0RQ{|Kl}g(@Bjce9~dJFfB*h}|Nejf{(t}e002Ay0DJ%dd;kFW008&^0Qdj_@Bjhu00ZCv1K<Dy-~b1}00+PT2Y>(%fB+AG03QGV9{>O!002G!06qW!d;kD^004Xd0Qdj^_y7R#00Hm-0q_6=-~a>Q001~286^n-{{R91@B{z+1ONYn_#eUW1M&C(`1k;Pd;lIk01qDk2akXU!{7tq@B`p}2jCz7-~<1_0srs=|NaB;KZD>0<KO}D@Bn=906zEtAAA50z5oZ`00ZxU0rTJh`S1Yz`~dtvf&LHw{saI10RQ{|5AXm0IUgA%2>|{80sr6w|M&y{{sZ_wf$#^x@B#4n0C@NSK70TlJ^%-w00ZxU0r$WF```fm@Bn^%06#teKc9d<$MApQ|NroR{`epKd;$1A0018V01p5F4}bs%zyJrp00ZCv1K<Dy@HhwXAOG+V|L_O@-~fNX0024=1{oB6_uqZ+000000000003Ut#-+TZ&5C|U>A0HndA0Ge!00000000000000VA0HncK0G`)cyMq4JSZO;5dZ)H1ONa4cmMzg@Bjcm-~a>vzyLq|00aNP03ZAS0sr6tAN~LU|KI=z{r~_E-~a$0zyJV0@BjcG`~UzC{{R33|9}7h|KI=sfA|0ZAN~LU2mgQo0sjC10R8{~06YKy00;m*C?5_N|NsB}|NsB{|NsB@|NsBs0000000000000000000000000000C3|Nr;@|Nrm*|Nr0r|NnphJ}4g=5r6;y0pI`t1NZ;{2mSy62mb&71OLDP0RQj+06+Wy01y5E00;ko00IBt004jB001Ar002LL00aL306+Wy0sp`NAN&9T|KI>0{s000-~bQ)002Mm004gg008g+009610000#85AT51NZ^|;D7&*|NQ(P&H#P@1K<EY00ZCvJ^%yY0DJ%kzySCF9{>a30DJ%sfC2ab9{>U106qW%-~c`V1K<EY00ZCv0000000003-~c`V1K<EY00ZCvJ^%nfFe)kw004i$00030{{R31|Nrm+0RR900094hKi~j=00H~}KL7w9fFA$=0q_ri002G%zyJUTf#3iD0Pyeu_&7W~0soE%jsXAjf#-mK|KK^mKLhv<a1Vff1N;NP4}kvx-~r%2z<2<758xgE9s{@sfCqr@0pJ1Pd%$=AcpmT%06q^K1K=Nr#{m2f=i%TV|NroK1OLzP4*-AT_yfQP;P3!=000009{>OV00ZCv0001d000O855NEq00H~}55NFF;2-b+2mk;0004jg_y7P0|M&m^03YxG002QDAtMR^1K<Dv1NZ;{0sH^}0sa600RMmh0DHgy0DbTP06h2r06shb03RO!01pR%01tz}00)8a00Y2y00ZDY00H1100Hm^fB^Ud-~f04@Bn-Od;mTGJ^&s74*(zk|G*Fb|KJb*|L_O@|NH~M03HM201tui00+VF00H3m008)W004Y^00167000l4000NT074-eBMN{2fFJ+-2mk+p|NroK0RA2T566H3@!$Y_cmN+B00+l_0rB7fe0Tsp9soZF|Nnvi|A2r0@E`yG2Y?6R-~fDh03V(J1LuGM`QQLPcmM~U00ZZM0QukmK6n5ho&X2ufCusa|M-9Z{2%}R2mky407D`jB?$lr`~U&}{s2G!`~(00@ISymgZKbEKL7w@@BjfH0005_000kw004Xd00+PT06qW!0q_6-4}bswd;kCg-~a$00002^000NT002G!00Hm-01tow0DJ%d0q_6-4}bswegFUg@Bjc0zyJh4003bA01pHF1NaaB|G+>0`~ZLdfB=8M002ZKA0rBX|9}Ah|L_6-|M&y{|M&-h5Bv`R1N<HU0r)%s0r+?T0r2nu1M%Ph1LME|2giT_2hRWi51s%3A3Oj6K6n5CeDDAO`QQKn^S}TD=YRkQ&j0`qo&W$JJOBWEcmM$S@Bjnx-~b21zyKeIfB=3E00aCU06*|Q|Nnr0|Na2~|L_6-{r~^~MIIO<3V;9pfB*h}|Nejf{&)ZYcmM!+004LZ0C)fZcmM!+004LZ0C)fZcmM!@|NMXd{D1%afB*b=004LZ0C)fZcmM!+004LZ0C)fZcmM!+004LZ0C)fZcmM!+004jg{(t}efB*h}|Na0*92Fx9fB*ac|KI=q|Nr-Z06YKz-~bN*0C)fczyKZq0Pp|@fB-xI0ssGx|NMXd<NyC2008g+2Y>)P00H0t4*&po00Y1P9smIF00)2oJOBaU01p5FcmM;y03HAU07oStB?$lr{r~_!|KI@s|M&s_|NH~~0sIH>06Y)C01O|10018V002J#002G!002G!004Xd004Xd004Xd004Xd004Xd004Xd004XdAO3s*AO3s*AO3s*AO3s*03Lh*03Lh*03JR703JR703JU803IIz03IKJ03Hv(03HYM06qi!0saC1|NH>||M&nu|G)qT{r~_-Bpf3OcmM(CfB+tN00HNK03LV%0q1}K9(Vu&=YRkncmM(CfB+tN00HNK03LV%0q1}K9)JJ;=l}oyfB*mI|Ns7Y00HNK03LV%0q1}K9(Vu&=YRkncmM(CfB+tN00HNK03LV%0q1}K9(Vu&=YRkncmM(CfB+tN00H0tNe%`h3VG+AdFP&a=bm}zo_Xh<dFP&a=bm}zo_Xhh07?!DEeZ#L;CLPff#7%^2Z7*t9tVNocpe9V;CLPff#7%^2Z7*t9tVNocpe9V;CLPngW&jlKR=J-;NSoNOCKF03U~kq<G=uZ9smd6@Bsb?fDgbt0Q>>q55Nxq`~Y|lzyrYi03Hv(0Py?(2amu2Jp2Fw|G)qb`~U!dzyJgP001BS008sw00)o206aec0pR=q4+HQ3cn`n>z&`*U0Q>;(1Mmlc55PPCKLOwX{0{&F@OS_Z!@vMP9smIR08ASfBMNu`0Pp|--~a=_00)2o4*&oj002Ay0C)fZ@Bjhe00Y1P2Y>(%0015U06YKycmM$K00H0t1Hb?WfB+8w03HAUJOBWA008g+0pI`wzyJq;01p5F9smG8|Nejf{Qv*?|Nrm+O(`KG3V#3qf4_hLKi}X0AMfx0ANTkG5BvTA2mS8=2fp*b1K)Yz1JAth0q5R40Q2u20P**a0C@Yuz&w57;5<I?cpe{kJRT3c9uEiJ2Zw|21IK~)f%Cxoz<c0*;630z@DK1Gcn9zgyaV_L-T?dq?*M!O_kaKZ`@jGIec%89KJWklA9w%&54->X2i^bx1K<EoBpf3OegFaI@Bkiv00HOt03LsU0q6Vx9)I8g=e__QdGG<}p8y_s_yOmSfF5{!0q2Ln9(X<h=Y!xLcpm}hfbbr84}s@^cpi8M!RLTH9(V)c=YSs`cmeU}fDfK{0Qu*D2i|x9f9HS${&)aC=YRqJcmNOQfB^n@00-azPbMNI2>=K9000mFzyJ^b`~V04|9}Jh5AXr_0R8~{01v=^00HnH004duzyJ?}-~a*e_y7QWd;kC+9{>OY=fD5}`S1V$K70TG51#-41Lwd10Qv9$06u&G01ux400Za1008;$002IG0018kfB*->-~a*e`~U#>9{>P;2jBo70Q>+Cz#o7Q-~;>*@Bn}R_y7<8`~U#|`~Uz4_y7O^P#qW}3V;6qfB)cr|L}kR_;>^ScmVu(0DgD?K6n5=cmO_l06usCK6n5=cmO_l0DgD?{CETWfB*P@|L}kR;D7%BcmM!+004LZ0C)fZcmM!+004LZ0C)fZcmM!+004LZ0C)fZcmM!+0000{CL$^c00;O001yAb01yBC00;m7fCKyw@B#P${s8;{55Rr^0q`FH0Dcd^01t!U00Hp$004Y^0018!000B$zyJXG@Bjcld;kCsp8x;@=fD5}`S1V$K70TG51#-41Lwd10Qv9$06u&G03Q#400+b100Hp)008(O004dm-~b;0`~VNYAAk?w1N;y00Du4Z01yBC0095|000O700003-~a#sd;kCd4}bsw0q_6-06qW!QXw283V;6q2mk&6fB*0Y|Nnq^0sIGm58!wJeg}X9;CKK&2Y>_McmO^JfCJ!o06qtR2jF-B{0D#^z<>Yv2mk&6fB(P-|Na1Y1MmlcAAooO{0D#sz<2;Y2Y>_McmN*<fC2D$01t<N0Qh(S2giT_e0Tr@=YRk{cmM(L08<_rB?$okfCK;h1ONYn|Nq1I2jlPnaqs{L@Bje#004Xd06qW!9{>OkfB*yF00H~}0RO-MKmGs@|L_6-{s2G!fC2yD00;O00Q>*|J^%n8fB*-;00ZCv0q_6-_y7R<004d90Dk@f{(t}eKmYy*|NH<y@Bjc*9UdbJ|NsB{|NsB*|NsBL|Ns5~4}bswJ^%m!_y7O{-~a#*fB*nK0002^000Bv000kw002G!008&^00ZCv01tow06qW!0Qdj^1K<Dv4}bswJ^%m!_y7O{-~a#*fB*nK0002^000Bv000kw002G!008&^00ZCv01tow06qW!0Qdj^097L!BntQd1OEU3f8YQQ`~U&}fB--600;g60RO-MANT+R{{R4g-~bQ&00IAi06*{m2mSy6|G)qr_y7a{004jB01x~C0snviKkxtt{r~{~zyKfk00aL30DbTP4?X|`=fD7bd;lL0zz5*|1NaaB{s8~~fDixR06*XW09GL(BMN)~03SX801ux400)P_00+b100ZIh00ZEB00Hnm008(8fB^UhzyN#$-~c=T_y9ftd;lK+9snNz4}cGV2fzow0q_UF0Qdvo0DJ-903QMH01trp00Y4I00HoP008(r002Hd0018!000k<000B;fB*sazyJV$zyJV0-~a$0-~a#z@Bjb<_y7O^_y7O^S1&Ci3U~kyzySN;0Db@m-v9^j0DSlWKY#<{zybaMA0Ge@@BsMu0QZ0ohrkEC0DK+*Jn#eH_yOmD9|yo5JOS`N0P)}tfba*0fP4qQJUj#7J_EtvJ^}C^4*~E8fbcjEfIbI-;CKP>cn=4_4}-vXJ^(x(0m1MA@bC{001uA<cz6JOcmv140pq|9J^&A%0D0g5ec%Jn00Zv;9{2zccmRLE0Dr&(`~U;|03YB0AK(E0004gg1NZ;~_y8Y(03Uz=`~U!0As-_OJ^%ptJ^%smJ^%;6d;lK+d;op`d;s_W_ygbo_z!>p_#XfP@O%IP@$div^WXpj|9}7k{r~_2`~Uz4@Bjb@zyJUrzyJV0fB*phfB*ykfB*;I0018!004X+008(t00ZDY01tpZ03QH+0DJ&^0q_8P1K<Go4}bvpJ^%pt`~U&*@Bjhu09hR#BMSHc0Qv9$2gBe19}j>4_#XfVz&-#U0Qdm-0q_UF1K=M34}kap9|ynyJ|6%8`1k+;_rL%H{{R3F_y7POzyJV00002^000Bv000kw002G!008&^00ZCv01tow06qW!0Qdj^1K<Dv4}bswJ^%m!_y7O{-~a#*fB*nK0002^00015Asr(MfB*mU|NsA=|Ns2||Nr0s06qW!1MmO<KL7v&@BjcG0005-0019=00H;_03Uz=0Qdj^4}bsw`~UzCzyJXJ000NT004Xd00-az0Db@f2jBnzJ^%m%-~a$W000B<002J#00Zy<03QGV0q_6-AOHXV|NsC0|NsC0|Ns5~TN4W_3IE^w|9|fR;5-L_@E!xecn<;KJO_aA9s|I54*}pj2Y~P%1HgC>0pL6bfbbpzz<3V<;5-NZ|KI!n003MN5hn`p0C)f%01p5MfC1nD@BnxK9smyj2Y><K0Pp~K03HAj00)2rzyR<7cmO;A4*&;%1Hb_A0C)gA01p5MfCIn)@BnxKJOCa52Y>^>0pI|506YL)6ALQ|fA9VOzwkZ>!1x~n;Cv5(@ID8?_#Xq{d=G)}J_o?~9|Pcg4}tJL2f+9r1K@lQf$%;D!2ADy@BROP0A45`4GI7czyJV0zyJXMzyJgPzyJ@=zyLoFzySOYzyt6Pzz@I=z#jkyz<dA)!QcP~$AAC_zyMzu83Z){|Nnpg|G)qL-~a#M0ALsl2?zKGz&ruq4*+-vfII=<0AU>%91;Ql01yAbAOG+l|M(sO_z(bm002Ay06qW!9smFy0RR36|NamE{vZGTKY$)S03Lh*9(VvgcmO_l06usCetZCaegOVI1O7k%-XH&-5C0wm_y7Q69vCGF_y7R-008&^0Qdj^_y7R-008&^0Qdj^_y7R-KLGgu!1@31`~Ud=f%yLb{QdxZ`~W`u06zEt9{2zs_y8aH03Y}OANT+t_y8aH03Y}OANT+s`~W`u06zWzeE$Ia|AF}X|M>a;@c94006zc#V;UA55&%EI2mio7|AYVj58ya{03+}K4}buC00Hm-2fzRx004LZ0pI`!fB+r<0C)fa@BjzE03QGVJ^%px00H;_gZK^)|M(C8;2-}05AXnF9vLMG000jF00)2o1Hb?Q-~a&d004LZ06YKy9smFj0DlL7|Kq^_`QZQl@cs|@d;$D?0De9IKRy5tp8yBX00ZZM0Q0~AdEfv%@Bkio01rF>2c7^2&wvBxzya~_0r>a;{5}BwAHn|z|M!9a^T2=c;1A#c0A(H-91;LOfB^sS0RR2~|Nnse58(I#@c00HcmN(e01rL@1Kt1u@Bjbz|Nr~{|NZ~}{_p?*cmM!C0018V01tow1K<Dw_y7QY00bYvJ_rB*0ssGifB%37`~U!E5fLN_0Dpl0!2jU?@O%I~06qX801to%z(4=r|L_0z|M)%t9{>-42fzd10q_9$0DJ&G03QGkfCs<>-~sRe_yBwWJ^&v84}b^21K<Jh003tm86^?`{s000$ASOz!T<f?{2%f71Nis={CEI<d;lLl01uu31J3{f=YRn7zyNvR06g#j9(Vu`J^&A&00+l_2jk!a@%RJye+T>@|K11x&jJ6(fIox400ZCv0q_6-@Bje#5CHrS0sII5`~&~|0RQ{|5AXm0XdV|N3HSg3@Bjng00+PT4}bt4002G!0DJ%d_y7U$egotG2habHzyBZbKR>`ee*ixG0DbTPd*A@~zya@o1K$7#z5ow=03P@NJ@5c~-~ji)0q=kV-v9@`01tcs9{2z~@Bn+@0QbNF-~ee21tbZ3-uHk203P?f?|a_&z3+S8_r33X-tYiw4GAs@2ZO=j@OS_K00001;P7}n9uEhD!Qk+CJRT1RgTdhNcsw2t2ZO=j@OXSa9}f?|-_OT@0Bal=BnkKc0Qdj^_y7R-008&^0Qdj^_y7R-008&^0Qdj^_yB(R0QmR;@c0AZ_z%GNAAtBj0Qi0Y`1k<%@BsVZ0RO-M|G)tM-~jvZ0QvX;`1}C)egODC0Qet(_z%GN2jKVv@c04v_yGL)06qY04Fx0#d*1iG?|a_&z3+S8_r33X-uJ!ld*1K>Z7(Mq5&%B{AA#}zfd9ki|AYU>-~W&Q&-gz)AD_S<;19n5KY$;806zd8_yBwWJ@5ed0Ds^C@Bsh71K<JwfCs<>{{Rnw2mSyb01x~CJ^&y10DJ&H@BsJ#f8YV|0RO-P-~s=D2fzdW01to%{s12U5BvZ=03Y}Od;mZ20QdlZ-~sRe_yBGm7aI})KLPRogXjOp-~W&JAD`eKKY$;806zEtJ@5c~-~ji)0q=kV-v9@`01tcs9{2z~@Bn+@0QbNF?|=i}00+JR4}1U~_y9fd0DIs7@BnWe85|M-e*ggg@B#n)0ssF2{2##h1Mv6&_<R69d;lLl00*A{1J3{f_kaNVzyN*V06y>lA9w%{z5oZG00Yl}1LNQU@$dogd;$1BgZK~s_yhm=0Dt%Z58wa*a2^;X5&%B{`2WE9|M2_&`2T_U{{Z~{0DSxaKKuYa_y8XG03Y}OANT+t_y8aH03Y}OANT+t_y8aH03Q4RKKuYa{s4Uc0Q~=f`1}9(`Ty|v|G@Y^0Qdj^_y7R-008&^0Qdj^_y7R-008&^0Qdj^0C64}B@zJs00IBUf&cTt|NY_oAMp4C`1k<)d;orY03SX851s%A&j11EfB^Hr0D0g5Jn#S>cmNMP01ux42hV^5<KP4F@B#RI0sKFM{ty4}1OMlM|Kq?P!QcP@@BjdK002Ay03HAU4*&oMfB*x)00H0t0Pp~E6c8H{06+Nu`TzU>|A7Ah{s8;{`~dg>_yG6-_yG6-_yG6-_yG6-_yG6-_yG6-_yG6-_yG6-_y7QN85JB70sa7g{s;f~fB(bq9zFmO-~bN*0C)fczyKcr0Dk}j|9}twfFJ(=AN&9h@Bj~h06qW#@Bj~h0DS-l&j9{^|KtDu5C7l~_y7QO6A>W{9{>-42fzd10q_9$0DJ-e|NsC0|NsBv-~sRe_yBwWJ^&v84}b^21K<Jh0QdlW06qX800)2rzyaU@_yB+WAN~jb0RMmhbsiTR6Yu~%-~fBT0QZ0a?*Ied00+DP4|o6`@BlsF0DHgy_kaQK00Z6t2fP3ecmN*o06p*k```ihzys%i56^%<pTYkh|K1<}JRkUY55NEbb{rZS6L<gz-v9yUzySF006snd4+nq;!QcV#d;oY406qiY4*>WFz#akc2f%m$@IC-M4*(B?zyaa#0DO1=A3gvB&wv2?zyKfc00;O00sa60KY#!azyJVuCnOpZ@B#1v?|>hG9(V)z1LuH0fINHy_yfnlKfruE2fPQvz<a=WJ_no!f#7lA_#O`)4*}ru;P4+04i5nE;PLPe9uFP>@!)ab51a>{0DHiD;0L@1ya0c|Kfnk01N;C#fIq+k_yhO=KY$;A1MmU(03QG!fB<+L8X6Nm01uCV2f^?I;64EO2f%y*@IC-O9{>l(zySN;06*{m2lxO0{r~_!000lb00;O01OEU4```e4_y9g103QS32f%y-;2#0-1K{`od_DjVp8x~k0C^l5BolZ52j2hz=fD8?@BltO01pR%2f^?G;5-2M4*)y^;12+J2f!Zz-~+(;0Ps8jJ`Vr~hrj{x-~c@M01rF>0q+0+f4~4A-~a>o008^|03QGV2fzRU-~a&l002Ay03QGV2Y>(r-~b=+00;a40sa60egFUfdKnfP6Mz5t|NrOz|DXT<008&^2fzS600Hm-4}buC00ZCv4*&po00Y1P9{>RO00+PTJ^%sm01towJOBaU01yBFzyJRK|NH;{-~f9c6D$b;58wy<0snx1@DG3i-~fC84}byi06qW*zySCF9{>a30DJ%sfC2CTJOB@X1Mm<00sa6#zz6;S2jBpF00)2o_y8XO1K<FB01tox@Blsl2fzUM03QGY-~c=T2fzUT;1B!&|9}VZ0DKSyFbVg)?|a_&z3+S8_r33X-uJ!ld*1iG?|a_&z3+S80DT`5ED8JoAMgYJ0Ds^BegFr+0C)fo00H0tJOBrP0Pp}F00Y1PcmNLo0pI{W00+PTegFsl0Dr&__yhj{`~W@x2fzUE03HAXzyNpv4*&t+06YK(fB^6S9smQt0Qdku0RO-r_yhg`egFUfekdOa82|tP00-az2!H$lbN~MX@Bjb*-+}-CH~@e6U;rP$00000AQUhx1RnqY|NsC0|NsC0|NsC0|NsC0|NsC0AQKoA1RnqY|NsC0|NsC0AR-(O4ipE#KfwRv|HuE||G)o#{{Q^{`Tybnf&Kva03a9-2Mh`hJaOaCo_zW9=fEHt4+snjK0ZD^K0JJQcyMswARHMH3<?eh4+Dn-$ARO)<KXe&`S5)BK71cO51$9XARQSI3<^FEp9jx_=fU&f@!<LJc<?-U95^044jcyn0M{rS8xRlx0E2)49DD!+=imT-KL8KG_yPD2z&`+f2jBzn`~V-HfB^sS00;g606)M00r&s_KfnM7{r~{~@Bkm5fCKRS0DcGH55PYG_yPDo01wCD0DgP`1LJ@I91s8ifB>)<5Dy6l;1BRW_&hv#9&iqD4sZ@|4sZ^59y~lh{2%ZK-~hJ|1_l}X@4oxs"
FONT_BOLD_B85 = "05AY80BHaq5dZ)H03j9%BMN_?=lTABpXd4hf1l_1{(qn6`Tl>O=lT9W55w^M00001{(qn6`Tl>O=lB3384(Q%d>=j!p9jx_=fU&f`S5)BK71cO51$9mgXh8U03#?OA`1Wq!2AFK@IC+l{11QtJ_FzY4}tgq1K@lB0r(#P0DK3)03QSJ2mk;7@&Et-{D1%d{~!PV|HuFT|L_Okd;kIP9{>P+55NE)1K<D;!1w?I;C=xA|Ns6!|NsAw|NsBv|NsB^|NsB~0DKRC06zoZ01trp00ZED008(O004dmzyKcs@BjzE`~U&)J^%m!Bq1Ct2>=fO008g+01p5F0Pp|+4*&oU|9}Vo|A7Dh_#glOga7~df6otx`0xmS4*&=7@Bn|000;c=0Du1g2mk&6KmYs#|NrnG|Nnr0|NH>||G)tM{s0eu-~jRd01qGF0Py}m4-e-6@&11gKga+7{D1%dhyVZZKmYsyAN~LU4*&oF@Bjc00002+000jF008g+01p5F03|RkB?$re00Hm-KllI#zybgG06qW@|L_6$06!1F2fzXNKY%^}2jG4H_y8Y)_y@oMd<Wn^00HnHfcO9hz<vk703U()9{>P;2jKVs0r)?M-~a>g{2u@S5C7o!001BVgWv!FKlmR20019={0Hy=00ZEE@BjcG2mjyz0DK?+zyJf_{yzW!4~Ou6004X+f%pIe@O}s201tuq55NF?2jD*d0q`Gy_y7-peh1(HegXI&fC2Ca@O}UffDhyF06qX8|G)w80Dt}f55NF_@Blsl0Dk}gCMqT+2>=KF00030{{R37|NH;|KmYIm0ssHN00;m7002MmJOBXyfDix!{r~^~5BLB806*XW004i$00061fB*mk{r~^~AN&9S0RQ*_{0IN=2k<}t;2**N|G@tb`Tv9bKg0hI;r|Eze~0)V`Tif^KmYK5fPeqN{s8~}2lxU1_#f~C|G<CX2mS#6z#ser|AGJb2mk;7@DKn0|KK10|NnqL|MUL<KmP~*06*XW001Ws2Mr2*`Sa(`pFVu~^XI?-C>9SZ2?6{E@DJcWfPVq}1NaZ{AHaWr{{j35_z&<O;6K2B0saI02lx;0AK*X0e}Ml1{sH_0{0I0C@E_nGz(2r$fPVo00R92|0sI5_1NaB<2k-zX77r^4e*k{~{s8^~`~&<0_y_n0@DK1G;6K1WfPaAh0saI01N;a05AYx0Kfr&0{{j93{15OS;6K2Bfd2#h2lx;0AHaWr{sa66@DJcWfPVq}001f(7#0ZtJOBVZ002Ay06YL-JPdd|JpMd>f4%%4|L_O@zybdN0sjC8|G*#r@P9r0{yctoJUn1L3;;X;06YKyJOBVZ001i}A07_?55NEbAAkS=KL7v#egFUf`~Uy}_y7O{@Bjb@-~a#*zyJUrfB*nL0001f01yBF|KI=r|G)qL|9}7g{{R2~{r~^}_y9iu004df008^|00H;_00Zy<00-az01v<b03Uz=06zc#0Db@f0Q>*|0r&s_04x#=5F{Vr{vYA~AL0HV;r<`P{6B;Ee+S@x2fzR=6c7g-fBt{|fBt{|fBt{|fBpb25()_<f1l_1{(qn6`Tl=^051{}Ckg-$fCJzF_yBwW9{>ly1K<Go06qX8fCs<<@BsV(J^&AZ2jBtl0DJ&H01toz-~jjld;lK+2fzd10Qdkt03Uz{zya_8`~W@x4}b^Y0q_8P06zc^fB*n6As!_O03YB01OMOvKmXtX|Np=b|NnqL|NjC1hx`xt5BNXeAK?E0f5-d*{~z!J{C~g?`Tqbv=lB5szu*J@|9}ts{s2Gk_yGUE-~;~ufDilr06*vW0RNxx1O9)&5BdK9Kgaw5{}1p7{6F9y;QxUCf&Yj61ONZ<5C8vwAOHLSKmXtWKmGs!AK(B0F(Dcw3IYFs5C7l~|M&y{{s8~~fIt7>59jy;0sa60e}DiV-~b2s00I600Dpi0AK(B7_y7U^004i003YB02lxO1{r~`ffB+xh00;O00sa60e}DiV-~b2s00I600DpiV|NrOz|M~y_{(t}fpa1{o|Nr;^G9eoz2?76r1ONU3|Nrnm|NjU7|M36+{~y5r<G>I8U;zKf01x;80sjC1Ki~id`~U#|fB-+>00;a40sjC1f4~4A@Bjz?00IAi0RO-MKkxt#`~U<00095M06*{m5BvZJ{r~{~|No!=|MUO<{(t}f&;S4V|Ns9#|Nr0sGa(x#2?zhc2mk*7|Nr<O|Nn#k|L}kR{|^BF;Q$Z*0095M01x;80sjC1KfnMF_y7a{0095MAOG+J|M&oZ{s0gE_yPa_fIt8E00;j706*{m1O5O2f4~3-`~U#|fB-+}00;fR0sp@M|M&m@{Qv*|AOHWu|NrnG|M&nu_y7PjAs!<N00aL303ZAS0RQj+1OLDPAO8RV|NH<0|L_1G|G)tL{{RE?`~V-%@Bsclzyt9A03XBr0R9i~1Mok<AHe?r{sa66@DK1GfIq<g0RIE<1N;yF|Np=L|Nj5~|NH;{|L_0*|G)qL{r~{~000C0000m0002M00093000aC001xm005u^TBnm(O|AYVk_&@*uga7~dKmY%O|Nr<u|Nn#d002LL00Z~{06%~L1NZ;{KmWi3|NnqL|NaC2|L{Nm|AYVk_&x*w!T=Ba004jB00aI206*XW1O5O2Ki~iZ{r~_!<Nyc$Z~*_u;6MC-|Nn>o|L}kR{s;g6z(4=+06+Ku05%~VB?$lr`~U&}`~W}y_yhm{z(4=~1ONZ<Kll%U{{RRd@Bje+000m8004i000aC006*jW0snva5C8x0fB*l(|Ns9V|Nr>^@PFt30slYn5BdLqKkxhj|9{{Q`Tqca&-erWf50E{{sI3F_z(C$;QxXD|NIC4|G*#r`~ZLdzySaF00I60001{38zTz;|NsC0|NsC0|NsC0|NsC0|NsBL|Nrm+1N;C0|9}7=@Bjz=0094h03YB02mAm4{{R3#-~b2s00I9106)M05BLB9{{R4gzyJ^U00aI20Dr&$5AXm3{r~`ffB+xx00aC00RMmhAMgMN`~U#|fB-+>0000uAsr<N06*{mAOG+H|Nr10|Nnvi|NI~S|M368|A+hs{y)GU@%{k+kMIZle}F&3{saCG_&?x3|Na2~|KI`t`~V;S@B#n-;6MNWf&T~oAMg+G{{Vl__yPWZzz_5M0DqtG1N{GhALsl5|3B~#`2WHG$N&HQAOHX0fB*gg|Nr0v|NH<0{{R30IUyY-2>?I901yAb0ssF1AOHLT|NrnG|Np@M!~YNX5BPt;KjZuX{~zE7`2PSu=lB8tKfn+9{s8~a_y_)fz<=}qhyRcN|NKAy|Kb1t{{#R3_z(X-zz^g8001BG0093000;O00Dr&$2mA;Cf8clz{saI2;2;0~0RR8s2mk&6AOFArAMgMG06G&18WaEj|NsC0|NsC0fB*mh000000Du4g|NsC0|NsBM06P;4Arn96{QsZx{(sN;|3BaW000000000000;d4pY#5I&-wp9=lK3V$MF0ghv4`C06Zuk8xQ~h00aO40C)fZ2k-y@f8YQE|G)r0|9}Jk`~W}yzytsM03ZLr0ss5}2minT5B>lEAK(B0KkxtmfBXOdfByggAOFAr5C8B01ONO00RR6006+hL01y8F00;g600H~}004LZ000mGJt!X$7XSbM{r~^}`~Uy{_y7O@@Bjb*-~a#rfB*mh00000000000000000007|NsB*|NsBr|NsBL|NsAg|Ns8~|Nr~|J}4g>5P$#x0pI`t1NZ;{2mSy65C4DwAOFAr5C8B01ONO00RR6006+i001yA*00aNv0095M004i000aL306+c!1ONB{KmWi3|NH<y|G)$P`~V;SzyLq~004jB008~~00H0t00IC20000#92O%A2mS#6{ty5DKmYvy|NH;{@4^4L0snvp`~V;D0Dr&%{s0g70Ds^E{{SEO0RO-T{s2Gl0RMmk`~V;D0Dr&%{{R30000000006100;a4AMgNwzybdN2mAmZ@Bn|n002NRDk=*A0Dr&$00IC100061|L_0+|Ns5~0RO;0-~fLB0sH_zfB-*$AAkS@@DIQM0DJ@B000kx@Bjb-@c04v_<TMA|Gp280RR7k=fHpe;CbL5hxi_N55WEhz60PNf&YQ{2jG9;egXI&_#c2i2fhcu4}tH2_ygd3;C=!4KKLJieh;1l;2(#_fcy{R;qV`a`S^SX|Ns0CfdBve1K=O~{s4Rd`1}ALfB*mh1MmO<004df00;mNzyJ;a0sH_DzyLqsAMgMN|Nr;^0Du4d000O7_y7O^AMgMG06`@sBMJZq{{R30Kl}gy1OMOv03ZJV0095|000mF-~a%B{{R37|NH;|KmXtW0sj9003Y}K0093V-~b2s|9}90$NT^T{2$-|Kj8m>0sja501xmV-~j)C|9}Vl1N;C#z#s4f{s8}gAOHXS0ssI1@DKn0|A2r0|NIC4|Nrnm|NsAi{s061AMgMl@c)1S|A+Vh1O9)&03Y-I0095L-~a>u074}mBMSfj@B{z<_z(a8_&@*u@c;k+<NyEvkN5}vKj07i|9~I!{s4c^_yPYv;0OHwfIs8@0soKx|NKAy|KR`s{{#R3{ty5E{6GKy`2T=E^Zo#T@Av@!zu*J@|9}ts{s2Gk_yGUE;0ONyfIs{H|Nqbb|NlS#|M>s^|HJ?P{15;CfB*nPBOfIR00aL306+iW0ssH-5C8w*KmY&0|NsAk|KL9l{{Rjj_y7cd-~a&szyJgP000O6000m8001BG002MW0095M00IAi00aL300;g601x~C01x;803YxG06*XW0Ds^B0RO-M0RO-M0snvi0snviL;t`7ga6<^1ONa21ONa01ONZ{0ssH-0RR7h06*{m07NJvBMSfj-~d1W|9}tw|M&y{|Nnsh|Nrnm|Ns6E_y_;P{s4dY|9}VnKi~lW&-eg8^Zoz_{QrOf|G(e>KkxVe5BvTA1OESj0RO+>06*{e01x~A00aL2fB^r$-~d1G_y8aK{s0I3|9}JkKi~lW&-eg;<Ng4D`2T=^{6GKy{ty5E{{#R3|A7Dh|A0UL|9}tw`~Uy|MIjm^3jhEAzyJU5|Nr~{|Nj5~|G)qL@Av=%{r~{~fB-+>01x;81O5O2|9}8L-~bQ*|MUO<{Qv*|KmY&F|Nry<|NQ@e06*XW5BLBB{r~{~fB-+>01x;81O5O2|9}8L|Nrm*|NH;{{{R2~zyJU5|Nr;^Mj;s^3jhEA|NsC0|NsC0|NsC0|NsC0{s0000094h0Dr&$Ki~i#@Bk0^00;a41ONa1|Ns8~|Nnpg|G)qL-~a#b_y7m|00aI20sjC1|9}90zyLqs03YxG5BLBF`~U;~00I910RMmhf4~4g-~a#sM<*gB2>=2AzyJsT{{RR7|L_O@|NaC2|Nnvi|Nr3s_y_oZ_y8Us_y7Tq`~Uz0{{R31|9}7hf8YQBAMgMG2mAm40sjC10RO-M06*{p|Nr~||Ns90KmY&05C7lr1ONB@0RR2}00IAh-~fN$_y8aC{{RR4|G)wNANT-&$NzvI@c;M^{2%}S{{#R3|G<C$|L_O@|M&oZ|L_0<|9}7hNGKp93jcrs|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi|Nnpi{{Tr63L^^tzwi70|G)41{{O%4`~LsG@B9A$zwi70|G)41{{O%4`~LsG@B9A$zwh_}N)iq&3J>@{;QxdE5BNXe|AYPy_&?zPgZ>ZrKj8m^{tx&+;QxdE5BNXe|AYPy_&?zPgZ>ZrKj8m^{tx&+;QxdE5BPuQ|3Ccy<Npu%KY;K6081q!BMSe31OFfJ0RO}O06*}5zz_Tn_yhj|{{a8MKj1&`2mBBG0RMyk03Y!Gzytn2@Bn|$`~VOC{{R91|G)r0|L_0@|NH;||Nj60AOG+G1ONX30Du4R01yBF00IC1@BlyO{{RR4fA9eRhyMT{@PF_F{s;d6f53n65BLZF0sjDh@IT-O{|Ed4fAIf+2mc@N0DtrT00;j708AemBMSe306*XW5BLBB{r~{~fB-+>01x;81O5O2|9}8L-~bQ!00aI20RMmhKi~il_y7a`0094h06*XW5BLBB{r~{~fB-+>01x;81O5O2|9}8L-~bQ!00aI20RMmhKmY&l|Nr~{|Nj5~|G)qL@Bjb!08KC`BMSfU01y8E_y8aN|M&nO{{Q#@KmPyx06+f!`~ZLc|Na1f{{Q{}fBygf0RR5~{{a8~|NjB~{{O#${r>;IgZcjdpTqh7|DVJ8{{N5X@&5mh=kfmkkMH6B|A+tK{{M&n!T$e)|H1zMga5()|AGI3{{Mmhf&Tx1{{jC0fd2vh|A77h{{Mh}0sjAh00I90fB*sh|9}7i{{Mgg0sjAh00I90fB*sh|9}7i{s2xWAR`L@-~s>t-~s>t@B#n-@B#n-_yPa__yPa_`~m;}`~m;}{sI60{{jF1{{jF1|AGJizk&b%zrp|ipTYnCpW*-ikKzCSkMaNihw=aahxz~igZcmef&Ksgf&KsgfdBvhfdBvhfPer0fPer0fIt8LfIt8LfFJ+=fFJ+=fDixwfDixwfCvBofCv8oPbnoO2>=8B00061{{R3#|Na02|Nr;^KmY&W1ONa3fIs{n{saGjKlmT`0RO@NfCK*z_y8aH|G)r$$Nm5V|3BaW5BdK90DsT;00aL2zyKfj{r~{~zwiJD{r`XfKkxhi0slYX01x^9004i__y7a`f8YQ=^Zx(={}1>8ANYUZ0RO@NfDil+{s8~rKl~s50RR90-~<2v{s0gE|KI>W|NZ~~fB(P$0Ds^B002-U9wQ3>|L_C<|M(C8|M)-u|M36+|KtDv|Ihdb|3Bal{{Mg<`~Cnw@Av@!zu*J@|9}ts{s2Gk_yPaF;1B-)fPeG<|Nqbb|NcM!|M36+|AYVk_z(a806*XW0RMmh1O5O25BLB8Ki~iW|9}7k{r~_E_y7Pu-~a&sfB*yj000m800000Q7I)W2>=8B00061{{R3#|Na02|Nr;^KmY&W1ONa3fIs{n{saGjKlmT`0RO@NfCK*z_y8aH|G)r$$Nm5V|3BaW5BdK90DsT;00aL2zyKfj{r~{~zwiJD{r`XfKkxhi0slYX01x^9004i__y7a`f4~4g^Zx(={}1>8ANYUZ0RO@NfDil+{s8~rKl~s50RR90-~<2v{s0gE|KI>W|NZ~~fB(P$06+c!000O00000V-~a#se}Di00sa6000;O0001B008%9&BMSfj@Bsh+{s8~~{{a90|A7Dh|G@wM|KR_C|KR_CKj8m>Kj8m>Kk)y6AMpQxKj8m>Kj8m>Kj8m>Kj8m>|G@wM|A7Dh{{a90`~d&|`~d&|{{a90|A7C2|A7C1|G@u%f8hUsKj8m>Kk)y6AMpQxANc=(5BUFp5B&dt2mJql2mb$n1OESj1OEV1BON6P0DtfRAOHLV|Nrnm|Nn#k|NI~S|Kb0De-HQocz=KZL;L^$AK(B1{{R37`~Uzy_y7U_`~VOC{s2G!{s8~~`~(00@DKn0z#sqq03ZMG01yAb01y5E03YxG0RMmh2mF8lKj#1e|2_a8@%{n-kN^MtfB*l(|Ns0S|Np>0|M&n8{r~^~R3RZF3jhEA|9}7g|G)qL|KI=r|L_0*|M&m@|M&nu-~a$0@Bjc0_y7P0`~Uz0{r~_0{{R30|9}7hf4~3$Ki~iWAMgMG5BLB82mAm41O5O20sjC10RMmh0Dr&$06*XW03YxG01x;800;a400aI200I910094h004i$002MW001BG000m8000O4000C200010Cm$pV|9}Jk{{RR7{s0gE`~V;S_y9lu@Bn}R-~j*szybgNfCK;k00;m601yBC03ZMO06+im0Du4B0RR8M0ssGi1ONX32mk&65C8lCAOH9OKmYImfB)bB|G(e^{(ry+{QrOt`TqbP^Zx*U<Ng5uhyMrv2mk;45C8x85C8w*2mk*72mky40RMmh09GX>BMSe301x~A0094=@Bjz=f4~4g<Ng2x{vYrFAMk&`0RMyj01x;d@Bn|nf4~R)1O5O%;2-b-{{Vl$AMgYI0RMmw_y_y|f53mh1O5a401x;d-~fNY{{RF25BLBN`2T<af5-d)0scSW01x~A004jA@Bjh-{{R3F|M&m^fB(P$0ss5}01yA*002M#00061@Bjc0|9}7hKl}gy0sp`N09Q3LBMN_j2mAm(&+q{MfCu^i03YxH|3Bad{{TPZ`~d&p2l#)0AN&CS5BLNBfIs2?0RQ+0{6F9y{{a63`~&ykAK-t$e*6dg5BMM7!2f~&1M~PF@E_oQKLh*&{tw6C|A2qP`1~L65BPr{!~OvO55f3<fFI%bKOgV|{yzuf{s4c^;QoKW2l@C9&+q{MKLPpv03Y|@KYzdj|NIC4_yB+Z0Dt}f2mjy?|G)tM`~m;?03ZK=KmPy&|KJDzzyLq|0Dt%Z2mgQ%{{R60@B#ne03ZGUKl}gz|9}Jk00013B_tyXKi~jA<Np8${vY@N|G@u%5BLxK0snx1;6LyK{saC1Kk$FR0soKu01x>8fB=8r@Bjz@{{R3#|KI=t|NH;|AOFAr0RQ*^00;j7004jR000mFfB*si`~UzS|G)qP|NZ~~fB*0R2mSv50RNx(03Z1OzybdU`~W}TKi~)c1OEVjz#s4r_yGTb|9}ttAMgNw!~OsR{(s;AKkxuqBP1gV|G)r$=llQ<{D0s8|HJ<PANW7;1OEa4fIsjL{0II3|G<C12mTNI06*dXfCK*@@BknC{{R60|KI=*|NH;|fB(P$1ONB{06+f#00IB-000mE00030zyJUT`~Uy|f4~3$2mAm40Dr&$00;a4004i$000O40001gzyJUT`~Uy|f4~3$2mAm40Dr&$00;a4004i$000O400015BOfCQfB*md|NsB_|NsB<|NsBz|NsBb|NsAh00;g603ZAS0DtfR0sp`N2mb&75BvZCKllIu|KI=v|9}7w{r~_!_y7QZ@Bjh-zyJsT001BS004jR0095s00aMk01y5E06+Ku0RP|s0sp`N2mb&7AOHXV|NsC0|NsC0|NsC0|NsC0|NsB^09zIhD+&Mq|NsC0|NsC0;6K2Bfd2vh1N;a05AYx0Kfr&0{{j93{0I0C@E_nmz<+@M0saI02lx;0AK*X0e}Ml1{sa66_z&<O;6MNW|NsC0|Nr;^ToMu|3itp&00+PU@Bn@Q4}b&U0Q>+S00+PU_y9ft4}b&U0DJ%+00+PT_y9ft4}b&k0DJ%+00-az_y9ft55NKN0DJ%+fCJzF_y9ft2fzXF0DJ%sfCJzF_yAoN4=V}(|NsC0|NsC0;6K2Bfd2vh1N;a05AYx0Kfr&0{{j93{0I0C@E_nmz<+@M0saI02lx;0AK*X0e}Ml1{sa66_z&<O;6MNW|NsC0|NsB^0A45{4GI7U-~a#*@BjcG_y7Pu`~U!d{r~{~{{R90e}Du0Kfnk058w~r2k;-j1Nc9H0Q`Oc0Db^p7#IXJ|NsC0|NsC0|NsC00ALsn2?u@v`~mm_;0M4TfIk3y0Qdl5AR8PK0RO-N|Nj90|M(yO|AYVk_<#TZ4}d@MfCK&j06)M02lxa3|AYVk@&Et+fB*mA|Nr~{0ssGiKmYIt|Na2~|G+>0_z(a8ga6<E|NH;{|3Ck~<NxRUKluNF`~Uy|Vj>+S3I6~92lxO0KfnM1{r~_E@BjdRfB*yh001B00093000;OVfIr9o0sepf5C8x8fB*l(|Ns9V{vZ7Rz(42y0slYX2mSv5KkxVf|9^lF`}_bu-{1lM{{SEN`~d&I;0OKx06*{i1O9*DAM^ji|DXT=`2YX^hxz~fKga*U{vY@N06zc#0Am~&91;K@_yGU@1ONUH|NbBU{vZGTKll!R-~xZZ0Dr&$|9}AhfB^r10RMmh|9}AhfB^r10RMmhf4~5LzyN>X0zdc;AOHRz|NamE{saI10RR2~ANT-dA{`|O000m0004i000aC003YB00RI302lxO0KfnM1{r~_E@CWdJfdAwC5C5Ow|Ns9F|Nr>^|NqDS5B`7PKlA<o|DW&&{r><z@Av@!f4~R({s2GU@B#k+fDiZl0Dr&W2mJqlKj-`b|3B~_`2WHG$N&HSAOHXGfB*l1|MUC@{~zEF-~a#sWg#6L5&%Eo01yAb0RR7hAOHRV|Nr<O|Nr3s!T*o=2mF7)ALIN0|G(e^{r~^}@Bjb*fB*mc|NsBr|Ns8~fB*;l001B00094h07w1+4j=pn@c;k+ga7~h5C8w*AOHRUfB%30Ki~iWW)&7B2>>7X1OMP3|A7Dg1ONCR|KNYX0sjC8_y8Z^2mk+{|Nejf`Tzgt|No!={s;H~AK(CgfC2sh2lxOV-~fMs0sa67_y8Z^0Dpi1{s0H~03YB0e}Do000;O0AK(CgfC2sh0B0f{B@zJs001BSe}Vt={2%}S;s5{tAOHXO|H1#y{0IJjz#sGe0RO+>1O5L1AMf}8|9`*-`~Cnw-|zwc|9}tk`~d%-@CW?=z<=Za2mc@c|M-9Z|H1$N{s;fh@E`ntfIox$002MX00I9F03Yyv1OJ2n|M(yO|G@wM{0IO4fDixh01x~C003wr8zc$;001B000aC00Dpi05AXm1{r~_!zyJsM0093003YCf1N=Yuf1m%4|Nr^_|NlS#|M&lg{{O&#-}ndn{s8}fz#s4U1O5I0f4{&F_xJ(+{{TPV;0OEs0RMl0AMfx3{r&)dzrYXo_yPX^06*X02mAa0|9^lV-~ee52_y;sf4|@F_xt<+002MV@Av!t{{Mf!-|zSP{r>-dzu)io`~Cj^f4|@00BR5oE(s6te}nuV;Qt5sKfnM0000C0AK?E7_&>q^5Ac73{2$=|2lzk1{txhfgZv-h{|ER#!Tt~Me}nuV;Qt5sf5-m+=l?(P{}1qf003(s9V7|=000O0002M000I6001xm00Dpi01N;C0AK(B0{{R37_y7Puzz_NU0RNBh5BPt8|AYJw_#fc^fd3Ep2l@YiKi~KP|Nnpw|M&oZ{{RF3`~V;S@Bsh+zz6^T06)+C0scSW5Agqhe}n!5{2%xq;D6x%0sn{i2mU|6ANl?Of8YRY5D6p+|9`*V@Av!t{{Mf!-|zSP{r>-dzu)io`~Cj^f4|@F_xt_+|9`*V-~eqhEE^I41NZ^>2l)Tsf8c+g{~!N{|Nr~{_<#TZ|NqDT|NsB|fAIhKf9L)O{{#Miz(3$W=llcy0seo$Kj0td`~&_0{(pc!z#r%M1N;I0e}F&0ALsZ3`~m)dfIq+==lBEs0seo0KfoX7_yha_{(pc!z#r%M1N;I0e}F&0ALsZ3`~m)dfIq+==lBEs0seo0KfoX00B#~18xjBm@E_s-!~FmJfB*l_|Nr^_|Np=IKllCv{{O%~-|z?f{s8}fz#s4M1O5I0f4{&F_xJ(+{{TPV;0OEs0RMl0AMfx3{r&)dzrYXo_yPX^06*X02mAa0{{R4QAsrkN06*XW5C7l+|Np=r|NjC1|NI~S|M368|Bw6!{(rz9^Zo$;zu*J^{{SEV_yGU^zz6^S06+im0ssGi5C8lCf8X#2{QrPI=l%o#ANW7;|NsAk|Nr<8|NnqL|M&oZ{{R4gzyJVnA{`|X00Zy``2XNP&;P;y|NjsF|M-9Z|KtC||DX5={Qtl|=llTwzu*V`{{TPl@B#mSfCu~h06*X01OESjANTwK|G(e|{r`Y}&-?@afB1j%|Ns9V|Nrp+|Nn>i|M)-0{{j97;1BQs0Dpi01N;C0AK(B0{{R37_y7PuzyJaM000m000000aUvZh5&-@H03ZB+f&cUTAOHX1|Ns9V|Nr>^!T-<v2mXJ+AM^eI|G(e|{r><T@Av@!f4~R({s2GU@B#k+fDiZl0RNxx2mJqlKj;1f{~!22`2YX^!~g&O5C8x0KmLD!|Kt1t{2$-|0RI302lxO0KfnM1{r~_E@BjdRfB*yh001B0009300CE@<8xjBm@9_WsKmYUp|NsC0|NrnW{s8~L5BLE8fDiZp|9}th0RI3F@Bse+5AXp001xm0{{Rp00RI3F@Bse+5AXp00001U9T^-F0snvp|NIC4|A+to$N&H1|Nrs+0r>s^2!8+oKY#!q_y7<8@CX0@0ssHtfB*Oo|NH>|{{R91fB-+h03YN45A)y;`Tzg?|Ns1d|NcM!{s;g306*{m0CX1?A`1uj03YB0e}Do000;O0AK(CgfC2shfB*ge|M&m@-~a!A|NZ~}@PB{-{s0H~03YB0e}Do000;O0AK(CgfC2sh2lxOV-~fMs0sjC8|M(yO;6ML>fBpdf_yGUl0Cgf98xwzkALsZ1{(pcU=lB8se}Et7_yPWZfFI}h0seo0ALsZ1{(pcU=lB8se}Et7_yPWZfFI}h0seo0Kj-)Z{(rzf=llo$f8qb*|Ns6!|Nr6t|NbBUpWuJ-{sH&^004F$9~u*XfCK#hfCu>h03Y%G06)S00Dpu00saU01N;a05BLx8AK)MGKfoX0{{TP1{s2G2`~ZKC@BsfG-~j(WfC2vh00IC000aN{00;l@00;lT01y9w01y8F03ZAS06+Ku06*XW0Cy}Z8WVqjKY)MV;2+>0=lBQs2l)R1{{j9#z<<F15AZ+mKg0YF{15Pdga3p4AK?Gt{s;Je_<w=^AHE;pKgZ9<_z&^(^ZWz+{Cxiae?K2Tz#s32@9+ov;s5vn|M-9Y06+c@|9}tw1OLDS|G@w70RQkm`~V;P2mb&E{sI4h0snx1-~fN%ANT+Ocpo1c6F<NQ_<z73@PEL6z<<I20Dpu00RNBp0RO+>0RR7h0RR2~0ss5}0srs-0sp`N1OI>k2mb&7AO8RVKmGs!|Na02|Na0E`~CnQ<NN@B$NT~R2mA;82mBB42lzkW5BUFp5BLCiA0H$We}Du0|9}Vh{{SE1{s2G0{s8}j`~m(4`~&<4_z&<8@E_n0@ISyG;Qs(0;r;+W!}tJykMID0pWp!hKY#%L{{R91`~U&}_y7a{@Bjn<zyJsTfB+Bv000mC001BO001B0002M0004gg00I6000;a40srs-1OMOv2mgQo5B>lEANT+OKfnM00D2r48WVs2|9}7gfB*k~|Nnpg|9}7g00;g62mAmJ_y8a906*XWf4~6$fC2vi1O5O9`~VO503YxGKi~j=zySaM|NsC0|NsC0|NsC0|NsC00DB@AEC~Py`~ZLW0srs^|KJb*z#s4cf4~6$fC2sh1N;C7_y7;^03YB0KfnNgfB^ph0sa67`~V;L2mjy?|9~I-06+c!fBpam{s0I300;O05AXmV-~d0s0Dpi0{{R9000aC02lxOF@Bkn106*XWKi~j={s8~{0RQ*^|L_1m-~fCQ1~3Tw@4ox*zWeXK`|rN{@4ox*zWeXK`|rN{@4ox*zWeXK`|rL0eIgeu3IBir|KJ1v;0OQU5C6ab|G)tMfB^ph0sa63`~U~|01xm0AK(B#zyN=M0RI31{s06100aL32mjy)|G)$PfFJ(=fBpdfzytmO2mAmJ@Bkm+06)M0e}Dl000I601N;C7_y7;^03YB0f4~9%0Dt}f|NH^}@B{zA2mAm40DdSR3mE_a000Nz00@8h0CWHU1MmO;|KI=r|G)qL|9%Jm{NMrq;eY^t0000003Z}FECwBa|NsC0=l}oz|Nejf|NsBz|NsC0{(t}f|NrOz|NsB~AQKoA1|5I@=l}kH|L6byfB)zI{vaYB5)l&t@B#k;|KNZ8KmVWq=l}ix|9}7A|M&m>|NcM!hyTI<;2-b-@Bknf5)2Ot1K@rK;QSxK{6B~Ie~0*ghxmVo_<w*P84?Q*3O~pA{~zQ0e~<D0KZo)BKL_FXJ^&ybAQ%q{1K>Uf;C=_-d=J3<AHn<|!Tdji_<x7^e~0*ghxmVo_<x7^e~0*ghxmVo_#ho17Y_;_;r>6v{C|h|{}1v0ALIN#$M}Db;r>6v_<slR{13zUKZoFc4}ka|1MmO<*C-tv5D)+WfxrL`9{>RP`~VN<@BsfGzz^_$0RI8}5AX-@{{SD)@Bn}R00IB-00;j703YxG0RMmh5B>lE|M&n8|KI@se}E71{s8|6_z&<O;Qj!AkKh6R{s0H_-~b;E003|x00961uow^!2?yXG@IU-N{Cqxm9`FzF5AYB04|pDYK7af_{2%xS-~hK03JDm0pXd4hf1l_1{(pb"

CANVAS_W = 1024
CANVAS_H = 1024

# Newsprint palette.
PAPER = (247, 243, 232)
INK = (20, 20, 20)
MUTED = (90, 86, 76)
RED = (176, 30, 36)
NAVY = (27, 58, 92)
GREEN = (30, 122, 52)
OCEAN = (214, 230, 238)
LAND = (232, 224, 200)
LAND_EDGE = (120, 110, 88)
GOLD = (176, 132, 30)


# ---------------------------------------------------------------------------
# Font decoding
# ---------------------------------------------------------------------------
class Glyph:
    __slots__ = ("advance", "w", "h", "top", "bits")

    def __init__(self, advance, w, h, top, bits):
        self.advance = advance
        self.w = w
        self.h = h
        self.top = top
        self.bits = bits

    def pixel(self, x, y):
        idx = y * self.w + x
        return (self.bits[idx >> 3] >> (7 - (idx & 7))) & 1


class Font:
    def __init__(self, blob_b85):
        raw = base64.b85decode(blob_b85.encode("ascii"))
        size, ascent, count = struct.unpack_from(">HHH", raw, 0)
        self.size = size
        self.ascent = ascent
        self.glyphs = {}
        off = 6
        for _ in range(count):
            cp, advance, w, h, top = struct.unpack_from(">HBBBB", raw, off)
            off += 6
            nbytes = (w * h + 7) // 8
            bits = raw[off:off + nbytes]
            off += nbytes
            self.glyphs[cp] = Glyph(advance, w, h, top, bits)
        self._cache = {}

    def _scaled(self, ch, px, sx=1.0):
        """Render one glyph at `px` em height -> (advance, w, h, top, rows).

        Rows are lists of 0..255 coverage values. `top` is relative to the
        baseline (negative = above it). `sx` squeezes horizontally
        (condensed type). Results are cached per (char, size, sx).
        """
        key = (ch, px, sx)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        glyph = self.glyphs.get(ord(ch)) or self.glyphs.get(ord("?"))
        scale = px / float(self.size)
        xscale = scale * sx
        adv = max(1, int(round(glyph.advance * xscale)))
        tw = max(0, int(round(glyph.w * xscale)))
        th = max(0, int(round(glyph.h * scale)))
        top = int(round((glyph.top - self.ascent) * scale))
        rows = []
        if tw > 0 and th > 0 and glyph.w > 0 and glyph.h > 0:
            # Integral image of the source bitmap for fast box averages.
            integral = [[0] * (glyph.w + 1) for _ in range(glyph.h + 1)]
            for yy in range(glyph.h):
                run = 0
                for xx in range(glyph.w):
                    run += glyph.pixel(xx, yy)
                    integral[yy + 1][xx + 1] = integral[yy][xx + 1] + run
            for ty in range(th):
                sy0 = ty / scale
                sy1 = (ty + 1) / scale
                y0 = int(math.floor(sy0))
                y1 = int(math.ceil(sy1))
                y0 = max(0, min(glyph.h, y0))
                y1 = max(0, min(glyph.h, y1))
                row = []
                for tx in range(tw):
                    sx0 = tx / xscale
                    sx1 = (tx + 1) / xscale
                    x0 = int(math.floor(sx0))
                    x1 = int(math.ceil(sx1))
                    x0 = max(0, min(glyph.w, x0))
                    x1 = max(0, min(glyph.w, x1))
                    if x1 <= x0 or y1 <= y0:
                        row.append(0)
                        continue
                    total = (integral[y1][x1] - integral[y0][x1]
                             - integral[y1][x0] + integral[y0][x0])
                    area = (x1 - x0) * (y1 - y0)
                    row.append(min(255, int(round(255.0 * total / area))))
                rows.append(row)
        result = (adv, tw, th, top, rows)
        self._cache[key] = result
        return result

    def measure(self, text, px, sx=1.0):
        """Width of `text` at `px` em height (horizontal squeeze `sx`)."""
        return sum(self._scaled(ch, px, sx)[0] for ch in text)

    def wrap(self, text, px, max_width, sx=1.0):
        """Greedy word wrap; returns a list of lines (never empty)."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if self.measure(trial, px, sx) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]


# ---------------------------------------------------------------------------
# Canvas: an RGB bytearray with simple drawing primitives.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def blend_px(self, x, y, color, coverage):
        """Blend `color` over the current pixel; coverage 0..255."""
        if coverage <= 0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        if coverage >= 255:
            self.set_px(x, y, color)
            return
        i = self._idx(x, y)
        inv = 255 - coverage
        self.buf[i] = (color[0] * coverage + self.buf[i] * inv) // 255
        self.buf[i + 1] = (color[1] * coverage + self.buf[i + 1] * inv) // 255
        self.buf[i + 2] = (color[2] * coverage + self.buf[i + 2] * inv) // 255

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = color[0]
                self.buf[i + 1] = color[1]
                self.buf[i + 2] = color[2]

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def draw_line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with round caps via stamped discs."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        radius = max(0, thick // 2)
        for s in range(steps + 1):
            x = int(round(x0 + (x1 - x0) * s / steps))
            y = int(round(y0 + (y1 - y0) * s / steps))
            self.fill_circle(x, y, radius, color)

    def fill_circle(self, cx, cy, r, color):
        if r <= 0:
            self.set_px(cx, cy, color)
            return
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, yy, dx * 2 + 1, 1, color)

    def draw_circle(self, cx, cy, r, color, thick=1):
        for t in range(thick):
            rr = r - t
            for angle in range(360):
                a = math.radians(angle)
                self.set_px(int(round(cx + rr * math.cos(a))),
                           int(round(cy + rr * math.sin(a))), color)

    def fill_polygon(self, points, color):
        """Scanline fill for a simple polygon given as [(x, y), ...]."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y_min = max(0, int(math.floor(min(ys))))
        y_max = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(points)
        for y in range(y_min, y_max + 1):
            xs = []
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    if y1 != y0:
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[k])), y,
                               max(0, int(math.floor(xs[k + 1])) - int(math.ceil(xs[k])) + 1),
                               1, color)

    def draw_polygon(self, points, color, thick=1):
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            self.draw_line(int(round(x0)), int(round(y0)),
                           int(round(x1)), int(round(y1)), color, thick)

    # -- text ---------------------------------------------------------------
    def text(self, font, x, y_baseline, s, px, color, align="left", sx=1.0):
        """Draw `s` with its baseline at y_baseline. Returns width drawn."""
        width = font.measure(s, px, sx)
        if align == "center":
            x -= width // 2
        elif align == "right":
            x -= width
        cx = x
        for ch in s:
            adv, tw, th, top, rows = font._scaled(ch, px, sx)
            gy = y_baseline + top
            for ty in range(th):
                row = rows[ty]
                for tx in range(tw):
                    cov = row[tx]
                    if cov:
                        self.blend_px(cx + tx, gy + ty, color, cov)
            cx += adv
        return width

    def text_lines(self, font, x, y_top, lines, px, color, leading=None,
                   align="left"):
        """Draw lines top-aligned at y_top; returns total height used."""
        if leading is None:
            leading = int(round(px * 1.25))
        y = y_top
        for line in lines:
            self.text(font, x, y + px, line, px, color, align)
            y += leading
        return y - y_top


def write_png(canvas, path):
    """Write the canvas as a deterministic PNG (filter 0, zlib level 9)."""
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.buf[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ---------------------------------------------------------------------------
# Content — every fact below comes from the research brief (NEWS-BRIEF.md).
# Nothing here is invented: names, numbers and dates are as sourced there.
# Stories dated 21-23 Nov carry their true date in the line.
# ---------------------------------------------------------------------------

REGIONS = [
    # (header, colour, [story lines])
    ("NORTH AMERICA", (27, 79, 114), [
        "CrowdStrike buys Zscaler, $43.9bn \u2014 Reuters, 23 Nov",
        "US to blacklist AI firm Megaspeed \u2014 Reuters",
        "Trump halts detonation of toxic explosives \u2014 AFP",
        "Democrats seal record House majority \u2014 AP, 22 Nov",
        "ICE detains family at Seattle airport \u2014 AP, 22 Nov",
        "FBI probes hack of crime database \u2014 AP, 21 Nov",
    ]),
    ("EUROPE", (108, 52, 131), [
        "Ukraine claims warship sunk off Libya \u2014 BBC, 23 Nov",
        "Drone-hit Sparta II reaches St Petersburg \u2014 Reuters",
        "Moscow warns Estonia near \u2018open war\u2019 \u2014 Reuters",
        "Zelensky: Russia planning new strikes \u2014 Reuters",
        "14 killed near Kyiv; boy, 7, saved \u2014 BBC, 23 Nov",
        "Russian dead 700,000+ \u2014 NYT, 23 Nov",
        "COP31 ends with no deal \u2014 BBC, Sun 22 Nov",
    ]),
    ("MIDDLE EAST", (125, 102, 8), [
        "Iran vows to defy US blockade \u2014 Reuters, 23 Nov",
        "Iran readies 14 tankers to defy blockade \u2014 TOI, 23 Nov",
        "Trump may hit Iran again in new year \u2014 MEF, 23 Nov",
        "Iran: US owes $290bn damages \u2014 Pakistan TV, 23 Nov",
        "Gaza now a \u2018toxic wasteland\u2019 \u2014 Oxfam report, 23 Nov",
        "Settler arson hits 5 West Bank villages \u2014 BBC, 23 Nov",
        "Gaza students win visas for Ireland \u2014 Arab News",
    ]),
    ("ASIA-PACIFIC", (176, 58, 46), [
        "Factory fire in Indonesia: 24 dead \u2014 Reuters, 23 Nov",
        "India pledges $1.6bn to Nepal \u2014 BBC, 23 Nov",
        "US $2.4bn defence aid to Philippines \u2014 PiQ, 23 Nov",
        "China subs can strike US mainland \u2014 PiQ, 23 Nov",
        "S Korea picks new foreign minister, intel chief \u2014 overnight roundup, 24 Nov",
        "S Korea minister quits in AI exam row \u2014 PiQ, 23 Nov",
        "Hong Kong building regulator after fire \u2014 PiQ, 23 Nov",
        "India mulls 20% rice export duties \u2014 Reuters, 23 Nov",
    ]),
    ("AFRICA", (30, 132, 73), [
        "Ebola in DR Congo tops 11,600 cases \u2014 WHO, 20 Nov",
        "Kenya\u2013DR Congo restore ties \u2014 OkayAfrica, 22 Nov",
        "US $170m+ health aid for 3 states \u2014 Semafor, 23 Nov",
        "African energy states gained $21.6bn \u2014 CREA, 23 Nov",
        "Drones hit UN site in Khartoum \u2014 Africanews, 22 Nov",
        "Zambia opposition leader on treason trial \u2014 Reuters, 23 Nov",
        "Nigeria attacks: 64 claimed, 5 confirmed \u2014 Reuters, 23 Nov",
    ]),
    ("LATIN AMERICA", (202, 111, 30), [
        "US drone helped capture \u2018El Chapo Isidro\u2019 \u2014 AP",
        "Cocaine gangs batter Colombian forces \u2014 WSJ, 23 Nov",
        "Brazil probes Vance-linked donors \u2014 Ace Dispatch, 21 Nov",
        "Flavio Bolsonaro flees to Florida \u2014 NPR, 23 Nov",
        "Bukele seeks third term \u2014 Breitbart, 20 Nov",
        "Colombia asks X to suspend Petro \u2014 MENAFN, 22 Nov",
    ]),
    ("SPORT & MORE", (46, 64, 83), [
        "CAS rules today on Senegal AFCON title \u2014 Reuters",
        "Arsenal v Dortmund tonight, 20:00 GMT \u2014 Reuters",
        "UK to host 2035 Women\u2019s World Cup \u2014 Reuters, 23 Nov",
        "Liverpool thrash Man Utd 4\u20130 \u2014 AllSports, 22 Nov",
        "Alcaraz wins maiden ATP Finals title \u2014 TOI, 22 Nov",
        "India v NZ first Test ends in draw; Pant 128 \u2014 TOI",
        "Chess: Gukesh v Sindarov begins \u2014 Education Times",
        "NHS AI breast screening trial begins \u2014 BBC, 23 Nov",
    ]),
]

# Columns of the region grid: which region indices go in each column.
COLUMNS = [[0, 1, 2], [3, 4], [5, 6]]

TIMELINE = [
    ("Mon 23 Nov", "Nvidia: Huang returns"),
    ("10:30", "Lisbon unions march"),
    ("Afternoon", "CAS rules on Senegal"),
    ("20:00 GMT", "Arsenal v Dortmund"),
    ("Today", "Chess title match begins"),
]

ALSO_TODAY = [
    "CAS rules on Senegal title",
    "Chess: Gukesh v Sindarov begins",
    "Lisbon unions march 10:30",
    "Sparta II reaches St Petersburg",
]

DATE_CHECK = [
    ("ICJ: Myanmar genocide ruling", "19 NOV"),
    ("Trump\u2013Xi\u2013Putin summit, Shenzhen", "19 NOV"),
    ("Kerch Bridge strike", "17 NOV"),
    ("Fiona the hippo dies", "19 NOV"),
]

DISAGREE = [
    "Nigeria toll: 64 claimed vs 5 confirmed",
    "Russian war dead: 700,000+ (NYT) vs 490,000+ tally",
    "US health aid: $170m (headline) vs $176m (text)",
]

# World-map pins: (number, lon, lat, short label for the legend).
PINS = [
    (1, -121.96, 37.37, "Nvidia HQ"),
    (2, 20.07, 32.12, "Benghazi"),
    (3, 27.00, 60.05, "Sparta II (hit 21 Nov)"),
    (4, 30.52, 50.45, "Kyiv"),
    (5, 30.71, 36.90, "Antalya (COP31)"),
    (6, 56.25, 26.57, "Hormuz"),
    (7, 34.47, 31.50, "Gaza"),
    (8, 106.32, -6.36, "Cikande"),
    (9, 85.32, 27.72, "Kathmandu"),
    (10, 120.98, 14.60, "Manila"),
    (11, -108.47, 25.57, "Guasave (held 20 Nov)"),
    (12, -72.50, 7.89, "Cucuta"),
    (13, 15.31, -4.32, "Kinshasa"),
    (14, 32.56, 15.50, "Khartoum"),
]

# Small cartographic offsets (px) separating the clustered pins around the
# Black Sea / eastern Mediterranean (2, 3, 4, 5, 7). The lon/lat above stay
# true; only the drawn discs are nudged so no two discs touch.
PIN_OFFSETS = {2: (-3, 2), 3: (-6, -7), 4: (5, -3), 5: (-4, 2), 7: (7, 3)}

# Simplified continent outlines (lon, lat). Schematic, not traced from any map.
NORTH_AMERICA = [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-115, 73),
                 (-105, 70), (-95, 69), (-90, 69), (-85, 66), (-80, 73),
                 (-70, 62), (-60, 60), (-55, 52), (-55, 47), (-65, 44),
                 (-70, 42), (-75, 38), (-76, 35), (-80, 32), (-81, 26),
                 (-84, 30), (-90, 21), (-87, 15), (-83, 9), (-90, 14),
                 (-95, 16), (-97, 16), (-100, 20), (-105, 23), (-110, 28),
                 (-115, 30), (-120, 34), (-124, 40), (-124, 48), (-130, 55),
                 (-140, 60), (-150, 60), (-158, 58), (-165, 60), (-168, 66)]
GREENLAND = [(-58, 64), (-55, 70), (-50, 74), (-40, 76), (-30, 76), (-22, 70),
             (-25, 68), (-32, 68), (-40, 64), (-50, 60), (-58, 64)]
SOUTH_AMERICA = [(-80, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
                 (-70, -18), (-70, -23), (-65, -28), (-58, -32), (-55, -35),
                 (-48, -28), (-41, -23), (-35, -17), (-35, -9), (-40, -3),
                 (-44, -2), (-50, 0), (-52, 4), (-58, 6), (-62, 9),
                 (-68, 11), (-72, 12), (-77, 8), (-80, 9)]
AFRICA = [(-17, 15), (-16, 20), (-15, 27), (-10, 31), (-5, 35), (0, 36),
          (10, 37), (12, 34), (19, 32), (25, 32), (30, 31), (32, 31),
          (35, 28), (37, 22), (39, 18), (43, 12), (48, 11), (51, 10),
          (46, 5), (41, 0), (40, -5), (40, -10), (37, -15), (35, -20),
          (33, -26), (28, -33), (20, -35), (17, -32), (15, -27), (13, -20),
          (12, -14), (13, -10), (9, -4), (9, 0), (9, 4), (6, 4),
          (0, 6), (-8, 5), (-13, 8), (-17, 12), (-17, 15)]
EURASIA = [(-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 47), (0, 50),
           (3, 52), (5, 53), (8, 57), (10, 58), (5, 60), (5, 62),
           (10, 64), (14, 67), (18, 69), (22, 70), (26, 71), (30, 70),
           (35, 68), (40, 67), (45, 68), (50, 68), (55, 69), (60, 69),
           (68, 70), (75, 72), (80, 73), (90, 75), (100, 77), (110, 74),
           (120, 73), (130, 72), (140, 72), (150, 71), (160, 70),
           (170, 67), (178, 65), (173, 62), (170, 60), (162, 56),
           (158, 52), (150, 51), (142, 52), (141, 48), (138, 46),
           (135, 44), (132, 43), (128, 38), (126, 38), (122, 36),
           (121, 32), (120, 28), (118, 25), (112, 22), (109, 20),
           (108, 18), (106, 11), (105, 9), (103, 8), (101, 6),
           (100, 8), (98, 12), (96, 15), (94, 17), (92, 21),
           (89, 22), (86, 20), (83, 17), (80, 15), (80, 10),
           (77, 8), (76, 10), (75, 15), (73, 19), (70, 21),
           (67, 24), (64, 25), (61, 25), (58, 25), (56, 26),
           (53, 27), (50, 29), (48, 30), (45, 29), (42, 29),
           (39, 30), (37, 32), (36, 36), (34, 36), (30, 36),
           (27, 37), (25, 36), (23, 36), (21, 39), (19, 42),
           (18, 40), (16, 40), (15, 38), (13, 38), (11, 39),
           (10, 42), (8, 44), (6, 43), (3, 43), (0, 40),
           (-2, 37), (-5, 36), (-9, 37), (-10, 36)]
AUSTRALIA = [(113, -22), (114, -28), (114, -32), (115, -35), (118, -35),
             (122, -34), (126, -32), (130, -32), (132, -32), (135, -35),
             (138, -35), (140, -38), (144, -38), (147, -39), (150, -37),
             (153, -32), (153, -27), (150, -23), (146, -19), (143, -15),
             (142, -11), (140, -14), (137, -12), (135, -12), (132, -12),
             (130, -13), (127, -14), (124, -15), (122, -17), (120, -20),
             (117, -20), (114, -22), (113, -22)]


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def draw_masthead(cv, reg, bold):
    cv.fill_rect(0, 0, CANVAS_W, 8, RED)
    cv.text(bold, CANVAS_W // 2, 50, "TUESDAY 24 NOVEMBER 2026", 38, INK,
            align="center")
    cv.text(reg, CANVAS_W // 2, 70,
            "WORLD NEWS FRONT PAGE  \u00b7  50 STORIES  \u00b7  7 REGIONS  "
            "\u00b7  EVERY STORY SOURCED", 15, MUTED, align="center")
    cv.hline(20, 76, CANVAS_W - 40, INK, 2)


def draw_hero(cv, reg, bold):
    x, y = 20, 84
    cv.text(bold, x, y + 13, "HERO  \u00b7  MONDAY 23 NOV  \u00b7  REUTERS / BBC / AFP",
            13, RED)
    cv.text(bold, x, y + 62, "HUANG IS BACK", 50, INK)
    cv.text(bold, x, y + 86,
            "NVIDIA REINSTATES ITS CEO \u2014 TRUMP: \u2018I MADE THE DEAL\u2019",
            18, NAVY)
    cv.text(reg, x, y + 106,
            "Reinstated 11 days after Huang quit. Trump called",
            15, INK)
    cv.text(reg, x, y + 124,
            "into the board meeting to push the return.", 15, INK)
    cv.text(bold, x, y + 144,
            "Shares +31%  \u00b7  Nasdaq +6.5%  \u00b7  S&P 500 +4.7%  \u00b7  Dow +3%",
            15, GREEN)
    # Surge chart, right side.
    cx, cy, cw, ch = 770, 84, 234, 128
    cv.fill_rect(cx, cy, cw, ch, (255, 255, 255))
    cv.draw_polygon([(cx, cy), (cx + cw, cy), (cx + cw, cy + ch),
                     (cx, cy + ch)], INK, 1)
    cv.text(bold, cx + 8, cy + 16, "NVDA  +31%", 14, GREEN)
    cv.text(reg, cx + 8, cy + 32, "11 days after quitting", 11, MUTED)
    pts = [(0, 88), (20, 84), (40, 90), (60, 70), (80, 76), (100, 60),
           (120, 66), (140, 40), (160, 46), (180, 24), (200, 28),
           (218, 12)]
    prev = None
    for px, py in pts:
        ax, ay = cx + 8 + px, cy + 8 + py
        if prev is not None:
            cv.draw_line(prev[0], prev[1], ax, ay, GREEN, 3)
        cv.fill_circle(ax, ay, 2, GREEN)
        prev = (ax, ay)
    cv.text(reg, cx + 8, cy + ch - 6, "12 NOV: QUITS", 10, MUTED)
    cv.text(reg, cx + cw - 8, cy + ch - 6, "23 NOV: BACK", 10, GREEN,
            align="right")


def draw_region_grid(cv, reg, bold):
    """Three columns of region blocks. Returns nothing; prints column
    heights when MAKEFUN_DEBUG is set (local check only)."""
    top = 230
    bottom = 620
    col_xs = [20, 352, 684]
    col_w = 328
    debug = os.environ.get("MAKEFUN_DEBUG")
    for ci, region_idxs in enumerate(COLUMNS):
        x = col_xs[ci]
        y = top
        for ri in region_idxs:
            header, colour, stories = REGIONS[ri]
            cv.fill_rect(x, y, col_w, 20, colour)
            cv.text(bold, x + 6, y + 15,
                    "%s \u2014 %d STORIES" % (header, len(stories)), 13,
                    (255, 255, 255))
            y += 22
            for story in stories:
                lines = reg.wrap(story, 12, col_w - 4, sx=0.88)
                for line in lines:
                    cv.text(reg, x + 2, y + 11, line, 12, INK, sx=0.88)
                    y += 15
            y += 4
        if debug:
            print("column %d height: %d (limit %d)" % (ci, y - top,
                                                       bottom - top),
                  file=sys.stderr)
        if y > bottom:
            raise SystemExit("region column %d overflows by %d px"
                             % (ci, y - bottom))
    cv.hline(20, 628, CANVAS_W - 40, INK, 2)


def draw_timeline(cv, reg, bold):
    y = 636
    cv.text(bold, 20, y + 14, "THE DAY IN UTC", 13, RED)
    x = 150
    seg_w = (CANVAS_W - 40 - 150) // len(TIMELINE)
    for i, (when, what) in enumerate(TIMELINE):
        sx = x + i * seg_w
        cv.text(bold, sx, y + 14, when, 12, NAVY)
        lines = reg.wrap(what, 12, seg_w - 12)
        ly = y + 28
        for line in lines:
            cv.text(reg, sx, ly, line, 12, INK)
            ly += 14
        if i + 1 < len(TIMELINE):
            cv.vline(sx + seg_w - 6, y + 4, 32, MUTED, 1)
    cv.hline(20, 676, CANVAS_W - 40, INK, 1)


def draw_map(cv, reg, bold):
    mx, my, mw, mh = 20, 686, 620, 192
    cv.fill_rect(mx, my, mw, mh, OCEAN)
    cv.draw_polygon([(mx, my), (mx + mw, my), (mx + mw, my + mh),
                     (mx, my + mh)], INK, 1)

    def project(lon, lat):
        px = mx + (lon + 170.0) / 360.0 * mw
        py = my + (85.0 - lat) / 145.0 * mh
        return (px, py)

    for poly in (NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
                 AUSTRALIA):
        pts = [project(lon, lat) for lon, lat in poly]
        cv.fill_polygon(pts, LAND)
        cv.draw_polygon(pts, LAND_EDGE, 1)
    cv.text(bold, mx + 8, my + 18, "THE WORLD TODAY \u2014 14 PLACES IN THE NEWS",
            13, NAVY)
    for num, lon, lat, _label in PINS:
        px, py = project(lon, lat)
        dx, dy = PIN_OFFSETS.get(num, (0, 0))
        ix, iy = int(round(px + dx)), int(round(py + dy))
        cv.fill_circle(ix, iy, 8, RED)
        cv.draw_circle(ix, iy, 8, (255, 255, 255), 1)
        label = str(num)
        size = 11 if len(label) == 1 else 10
        w = bold.measure(label, size)
        cv.text(bold, ix - w // 2, iy + 4, label, size, (255, 255, 255))
    # Legend under the map.
    legend = "  \u00b7  ".join("%d %s" % (num, label)
                               for num, _lo, _la, label in PINS)
    lines = reg.wrap(legend, 11, mw)
    ly = my + mh + 14
    for line in lines:
        cv.text(reg, mx, ly, line, 11, MUTED)
        ly += 13


def draw_date_check(cv, reg, bold):
    x, y, w = 660, 686, 344
    cv.fill_rect(x, y, w, 196, (255, 255, 255))
    cv.draw_polygon([(x, y), (x + w, y), (x + w, y + 196), (x, y + 196)],
                    RED, 2)
    cv.fill_rect(x, y, w, 24, RED)
    cv.text(bold, x + 8, y + 17, "DATE CHECK \u2014 NOT TODAY", 14,
            (255, 255, 255))
    yy = y + 24
    cv.text(reg, x + 8, yy + 15,
            "These recirculated today. They did NOT happen", 12, INK)
    cv.text(reg, x + 8, yy + 30,
            "on 24 Nov \u2014 so they are not on this page:", 12, INK)
    yy += 39
    for story, date in DATE_CHECK:
        cv.fill_circle(x + 14, yy + 8, 3, RED)
        cv.text(bold, x + 22, yy + 12, story, 12, INK)
        cv.text(bold, x + w - 8, yy + 12, date, 12, RED, align="right")
        yy += 17
    yy += 4
    cv.hline(x + 8, yy, w - 16, MUTED, 1)
    yy += 6
    cv.text(bold, x + 8, yy + 12, "WHERE SOURCES DISAGREE:", 11, NAVY)
    yy += 16
    for line in DISAGREE:
        wrapped = reg.wrap("\u2022  " + line, 11, w - 16)
        for wl in wrapped:
            cv.text(reg, x + 8, yy + 11, wl, 11, INK)
            yy += 13


def draw_also_today(cv, reg, bold):
    y = 922
    cv.fill_rect(20, y, CANVAS_W - 40, 34, NAVY)
    label = "ALSO TODAY:  "
    cv.text(bold, 32, y + 22, label, 13, (255, 235, 150))
    x = 32 + bold.measure(label, 13)
    rest = "   \u00b7   ".join(ALSO_TODAY)
    cv.text(reg, x, y + 22, rest, 13, (255, 255, 255))
    cv.hline(20, 960, CANVAS_W - 40, INK, 1)


def draw_footer(cv, reg, bold):
    y = 964
    cv.text(reg, CANVAS_W // 2, y + 12,
            "Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 NYT \u00b7 CNN \u00b7 WSJ "
            "\u00b7 Oxfam/CEOBS \u00b7 WHO \u00b7 FIFA \u00b7 CAS \u00b7 Times of India "
            "\u00b7 Semafor \u00b7 CREA", 10, MUTED, align="center")
    cv.text(reg, CANVAS_W // 2, y + 25,
            "OkayAfrica \u00b7 PiQ \u00b7 MENAFN \u00b7 NPR \u00b7 Breitbart \u00b7 AllSports "
            "\u00b7 Education Times \u00b7 Arab News \u00b7 Pakistan TV \u00b7 Africanews "
            "\u00b7 Ace Dispatch \u00b7 MEF \u00b7 overnight roundup", 10, MUTED, align="center")
    cv.text(reg, CANVAS_W // 2, y + 38,
            "Compiled Tuesday 24 November 2026, 00:20 UTC. Stories dated "
            "21\u201323 Nov are flagged with their true date. Every story on "
            "this page carries its source.", 10, MUTED, align="center")
    cv.text(bold, CANVAS_W // 2, y + 53,
            "50 STORIES  \u00b7  7 REGIONS  \u00b7  EVERY CLAIM SOURCED ON THIS PAGE",
            11, RED, align="center")


def main():
    reg = Font(FONT_REG_B85)
    bold = Font(FONT_BOLD_B85)
    cv = Canvas(CANVAS_W, CANVAS_H, PAPER)
    draw_masthead(cv, reg, bold)
    draw_hero(cv, reg, bold)
    draw_region_grid(cv, reg, bold)
    draw_timeline(cv, reg, bold)
    draw_map(cv, reg, bold)
    draw_date_check(cv, reg, bold)
    draw_also_today(cv, reg, bold)
    draw_footer(cv, reg, bold)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    if os.environ.get("MAKEFUN_DEBUG"):
        print("wrote %s (%d bytes)" % (path, size), file=sys.stderr)


if __name__ == "__main__":
    main()
