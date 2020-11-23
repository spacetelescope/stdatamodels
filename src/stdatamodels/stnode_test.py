from . import stnode
from  astropy.time import Time
def mk_test_object():
    exp = stnode.Exposure()
    exp['type'] = "WFI_CORON"
    exp['readpatt'] = "RAPID"
    exp['start_time'] = Time('2020-11-11T11:11:11.11')
    exp['end_time'] = Time('2020-11-11T11:21:11.11')
    exp['nints'] = 5
    exp['ngroups'] = 2
    exp['nframes'] = 99
    exp['groupgap'] = 1
    exp['frame_time'] = 5.0
    exp['group_time'] = 20
    exp['exposure_time'] = 1000.
    wfi = stnode.Wfi()
    wfi['name'] = 'WFI'
    wfi['detector'] = 'WFI01'
    wfi['optical_element'] = 'GRISM'
    rd = stnode.WfiImage()
    rd['meta'] = {}
    rd['meta']['filename'] = 'bozo.asdf'
    rd['meta']['telescope'] = 'Roman'
    #return rd, exp, wfi
    rd['meta']['exposure'] = exp
    rd['meta']['instrument'] = wfi
    return rd
    
