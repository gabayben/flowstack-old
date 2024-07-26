ROOT_KEY = '__root__'

START = '__start__'
END = '__end__'
IS_CHANNEL_WRITER = '_is_channel_writer'
HIDDEN = "core:hidden"

INPUT = '__input__'
WRITE_KEY = "__pregel_write"
READ_KEY = "__pregel_read"
INTERRUPT = "__interrupt__"
TASKS = '__pregel_tasks__'
PENDING_WRITES = 'pending_writes'
CHECKPOINTER = '__pregel_checkpointer__'
RESUMING = '__pregel_resuming__'

RESERVED = {
    INPUT,
    WRITE_KEY,
    READ_KEY,
    INTERRUPT,
    TASKS,
    CHECKPOINTER,
    RESUMING
}