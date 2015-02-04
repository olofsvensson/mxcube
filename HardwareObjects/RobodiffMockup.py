from sample_changer import Robodiff


class RobodiffMockup(Robodiff.Robodiff):
    def __init__(self, *args, **kwargs):
        Robodiff.Robodiff.__init__(self, *args, **kwargs)

    def init(self):
        for channel_name in ("_state", "_selected_basket", "_selected_sample"):
            fun = lambda x: x
            setattr(self, channel_name, fun)
           
        for command_name in ("_abort", "_getInfo", "_is_task_running", \
                             "_check_task_result", "_load", "_unload",\
                             "_chained_load", "_set_sample_charge", "_scan_basket",\
                             "_scan_samples", "_select_sample", "_select_basket", "_reset", "_reset_basket_info"):
            fun = lambda x: x
            setattr(self, command_name, fun)

        pass

    def load_sample(self, holder_length, sample_location, wait):
        return

    def load(self, sample, wait):
        import pdb
        pdb.set_trace()
        return sample

    def unload(self, sample_slot, wait):
        return
