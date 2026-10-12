"""Authored source-clock cue order for the clean, actually drawn ending poses."""
FF_BASE_TIMES=[290.290,290.470,290.665,290.830,291.010,291.190,291.391,291.530,291.690,291.870,292.070,292.260,292.380,292.510,292.640,292.770,292.940,293.120,293.360,293.630,293.940,294.250,294.570,294.900]
FF_KEYS=[]
for k,t in enumerate(FF_BASE_TIMES):
 FF_KEYS.append((t,f'endff{k:02d}'))
 next_time=FF_BASE_TIMES[k+1] if k<23 else t+.4
 group='a' if k<12 else 'b';index=k if k<12 else k-12
 FF_KEYS.append(((t+next_time)/2,f'endffmid_{group}{index:02d}'))
STAR_KEYS=[(290.290,'endstar00'),(290.650,'endstar01'),(290.700,'endstar02'),
 (290.740,'endstarmid00'),(290.780,'endstarmid01'),(290.820,'endstarmid02'),
 (290.860,'endstarmid03'),(290.900,'endstarmid04'),(290.940,'endstarmid05'),
 (290.980,'endstar03'),(291.025,'endstar04'),(291.070,'endstar05'),
 (291.115,'endstar06'),(291.160,'endstar07'),(291.205,'endstar08'),
 (291.500,'endstar09'),(292.200,'endstar10'),(293.250,'endstar11')]
