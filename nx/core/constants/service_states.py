STOPPED  = 0           # Service is stopped. Surprisingly.
STARTED  = 1           # Service is started and running
STARTING = 2           # Service start requested.
STOPPING = 3           # Service graceful stop requested. It should shutdown itself after current iteration
KILL     = 4           # Service force stop requested. Dispatch is about to kill -9 it
