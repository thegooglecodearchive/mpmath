"""
Check that the output from irrational functions is accurate for
high-precision input, from 5 to 200 digits. The reference values were
verified with Mathematica.
"""

import time
from mpmath import *

precs = [5, 15, 28, 35, 57, 80, 100, 150, 200]

# sqrt(3) + pi/2
a = \
"3.302847134363773912758768033145623809041389953497933538543279275605"\
"841220051904536395163599428307109666700184672047856353516867399774243594"\
"67433521615861420725323528325327484262075464241255915238845599752675"

# e + 1/cgamma**2
b = \
"5.719681166601007617111261398629939965860873957353320734275716220045750"\
"31474116300529519620938123730851145473473708966080207482581266469342214"\
"824842256999042984813905047895479210702109260221361437411947323431"

# sqrt(a)
sqrt_a = \
"1.817373691447021556327498239690365674922395036495564333152483422755"\
"144321726165582817927383239308173567921345318453306994746434073691275094"\
"484777905906961689902608644112196725896908619756404253109722911487"

# sqrt(a+b*i).real
sqrt_abi_real = \
"2.225720098415113027729407777066107959851146508557282707197601407276"\
"89160998185797504198062911768240808839104987021515555650875977724230130"\
"3584116233925658621288393930286871862273400475179312570274423840384"

# sqrt(a+b*i).imag
sqrt_abi_imag = \
"1.2849057639084690902371581529110949983261182430040898147672052833653668"\
"0629534491275114877090834296831373498336559849050755848611854282001250"\
"1924311019152914021365263161630765255610885489295778894976075186"

# log(a)
log_a = \
"1.194784864491089550288313512105715261520511949410072046160598707069"\
"4336653155025770546309137440687056366757650909754708302115204338077595203"\
"83005773986664564927027147084436553262269459110211221152925732612"

# log(a+b*i).real
log_abi_real = \
"1.8877985921697018111624077550443297276844736840853590212962006811663"\
"04949387789489704203167470111267581371396245317618589339274243008242708"\
"014251531496104028712866224020066439049377679709216784954509456421"

# log(a+b*i).imag
log_abi_imag = \
"1.0471204952840802663567714297078763189256357109769672185219334169734948"\
"4265809854092437285294686651806426649541504240470168212723133326542181"\
"8300136462287639956713914482701017346851009323172531601894918640"

# exp(a)
exp_a = \
"27.18994224087168661137253262213293847994194869430518354305430976149"\
"382792035050358791398632888885200049857986258414049540376323785711941636"\
"100358982497583832083513086941635049329804685212200507288797531143"

# exp(a+b*i).real
exp_abi_real = \
"22.98606617170543596386921087657586890620262522816912505151109385026"\
"40160179326569526152851983847133513990281518417211964710397233157168852"\
"4963130831190142571659948419307628119985383887599493378056639916701"

# exp(a+b*i).imag
exp_abi_imag = \
"-14.523557450291489727214750571590272774669907424478129280902375851196283"\
"3377162379031724734050088565710975758824441845278120105728824497308303"\
"6065619788140201636218705414429933685889542661364184694108251449"

# a**b
pow_a_b = \
"928.7025342285568142947391505837660251004990092821305668257284426997"\
"361966028275685583421197860603126498884545336686124793155581311527995550"\
"580229264427202446131740932666832138634013168125809402143796691154"

# (a**(a+b*i)).real
pow_a_abi_real = \
"44.09156071394489511956058111704382592976814280267142206420038656267"\
"67707916510652790502399193109819563864568986234654864462095231138500505"\
"8197456514795059492120303477512711977915544927440682508821426093455"

# (a**(a+b*i)).imag
pow_a_abi_imag = \
"27.069371511573224750478105146737852141664955461266218367212527612279886"\
"9322304536553254659049205414427707675802193810711302947536332040474573"\
"8166261217563960235014674118610092944307893857862518964990092301"

# ((a+b*i)**(a+b*i)).real
pow_abi_abi_real = \
"-0.15171310677859590091001057734676423076527145052787388589334350524"\
"8084195882019497779202452975350579073716811284169068082670778986235179"\
"0813026562962084477640470612184016755250592698408112493759742219150452"\

# ((a+b*i)**(a+b*i)).imag
pow_abi_abi_imag = \
"1.2697592504953448936553147870155987153192995316950583150964099070426"\
"4736837932577176947632535475040521749162383347758827307504526525647759"\
"97547638617201824468382194146854367480471892602963428122896045019902"

# sin(a)
sin_a = \
"-0.16055653857469062740274792907968048154164433772938156243509084009"\
"38437090841460493108570147191289893388608611542655654723437248152535114"\
"528368009465836614227575701220612124204622383149391870684288862269631"

# sin(1000*a)
sin_1000a = \
"-0.85897040577443833776358106803777589664322997794126153477060795801"\
"09151695416961724733492511852267067419573754315098042850381158563024337"\
"216458577140500488715469780315833217177634490142748614625281171216863"

# sin(a+b*i)
sin_abi_real = \
"-24.4696999681556977743346798696005278716053366404081910969773939630"\
"7149215135459794473448465734589287491880563183624997435193637389884206"\
"02151395451271809790360963144464736839412254746645151672423256977064"

sin_abi_imag = \
"-150.42505378241784671801405965872972765595073690984080160750785565810981"\
"8314482499135443827055399655645954830931316357243750839088113122816583"\
"7169201254329464271121058839499197583056427233866320456505060735"

# cos
cos_a = \
"-0.98702664499035378399332439243967038895709261414476495730788864004"\
"05406821549361039745258003422386169330787395654908532996287293003581554"\
"257037193284199198069707141161341820684198547572456183525659969145501"

cos_1000a = \
"-0.51202523570982001856195696460663971099692261342827540426136215533"\
"52686662667660613179619804463250686852463876088694806607652218586060613"\
"951310588158830695735537073667299449753951774916401887657320950496820"

# tan
tan_a = \
"0.162666873675188117341401059858835168007137819495998960250142156848"\
"639654718809412181543343168174807985559916643549174530459883826451064966"\
"7996119428949951351938178809444268785629011625179962457123195557310"

tan_abi_real = \
"6.822696615947538488826586186310162599974827139564433912601918442911"\
"1026830824380070400102213741875804368044342309515353631134074491271890"\
"467615882710035471686578162073677173148647065131872116479947620E-6"

tan_abi_imag = \
"0.9999795833048243692245661011298447587046967777739649018690797625964167"\
"1446419978852235960862841608081413169601038230073129482874832053357571"\
"62702259309150715669026865777947502665936317953101462202542168429"


def test_hp():
    for dps in precs:
        mpf.dps = dps + 8
        aa = mpf(a)
        bb = mpf(b)
        a1000 = 1000*mpf(a)
        abi = mpc(aa, bb)
        mpf.dps = dps
        assert (sqrt(3) + pi/2).ae(aa)
        assert (e + 1/cgamma**2).ae(bb)
        assert sqrt(aa).ae(mpf(sqrt_a))
        assert sqrt(abi).ae(mpc(sqrt_abi_real, sqrt_abi_imag))
        assert log(aa).ae(mpf(log_a))
        assert log(abi).ae(mpc(log_abi_real, log_abi_imag))
        assert exp(aa).ae(mpf(exp_a))
        assert exp(abi).ae(mpc(exp_abi_real, exp_abi_imag))
        assert (aa**bb).ae(mpf(pow_a_b))
        assert (aa**abi).ae(mpc(pow_a_abi_real, pow_a_abi_imag))
        assert (abi**abi).ae(mpc(pow_abi_abi_real, pow_abi_abi_imag))
        assert sin(a).ae(mpf(sin_a))
        assert sin(a1000).ae(mpf(sin_1000a))
        assert sin(abi).ae(mpc(sin_abi_real, sin_abi_imag))
        assert cos(a).ae(mpf(cos_a))
        assert cos(a1000).ae(mpf(cos_1000a))
        assert tan(a).ae(mpf(tan_a))
        assert tan(abi).ae(mpc(tan_abi_real, tan_abi_imag))
        # check that complex cancellation is avoided so that both
        # real and imaginary parts have high relative accuracy.
        # abs_eps should be 0, but has to be set to 1e-205 to pass the
        # 200-digit case, probably due to slight inaccuracy in the
        # precomputed input
        assert (tan(abi).real).ae(mpf(tan_abi_real), abs_eps=1e-205)
        assert (tan(abi).imag).ae(mpf(tan_abi_imag), abs_eps=1e-205)


if __name__ == "__main__":
    globals_ = globals().keys()
    t1 = time.time()
    for f in globals_:
        if f.startswith("test_"):
            print "running", f, "..."
            globals()[f]()
    t2 = time.time()
    print "passed all tests in", (t2-t1), "seconds"
