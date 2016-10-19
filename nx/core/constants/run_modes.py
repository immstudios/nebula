RUN_AUTO    = 0    # First item of this block is cued right after last item of previous block
RUN_MANUAL  = 1    # Playback stops at the end of the last item of previous block
RUN_SOFT    = 2    # First item of this block is cued if previous block is running and current_time >= scheduled_time
RUN_HARD    = 3    # First item of this block starts immediately if previous block is running and current_time >= scheduled_time
