SECTIONS
{
    /* Place .hotpatch_context immediately after .data */
    .hotpatch_context :
    {
        . = ALIGN(32); /* Ensure 32-byte alignment */
        __hotpatch_context_start = .;

        *(.hotpatch_context*); /* Include all .hotpatch_context symbols */

        . = ALIGN(32); /* Final alignment */
        __hotpatch_context_end = .;
    } > RAM

    __hotpatch_context_size = __hotpatch_context_end - __hotpatch_context_start;
    __hotpatch_context_load_start = LOADADDR(.hotpatch_context);

    /* Place .hotpatch_slots after .hotpatch_context */
    . = ALIGN(32);
    . = ALIGN(1 << LOG2CEIL(__hotpatch_slots_quarantine_size));
    __hotpatch_slots_quarantine_start = .;

    .hotpatch_slots :
    {

        __hotpatch_slots_start = .;

        *(.hotpatch_slots*);

        __hotpatch_slots_end = .;
    } > RAM

    .hotpatch_quarantine :
    {
        //. = ALIGN(32);
        //. = ALIGN(1 << LOG2CEIL(__hotpatch_slots_quarantine_size));
        
        __hotpatch_quarantine_start = .;

        *(.hotpatch_quarantine*);

        //. = ALIGN(32);
        //. = ALIGN(1 << LOG2CEIL(__hotpatch_slots_quarantine_size));

        __hotpatch_quarantine_end = .;
    } > RAM
    . = ALIGN(32);
    . = ALIGN(1 << LOG2CEIL(__hotpatch_slots_quarantine_size));
    __hotpatch_slots_quarantine_end = .;

    __hotpatch_slots_size = __hotpatch_slots_end - __hotpatch_slots_start;
    __hotpatch_quarantine_size = __hotpatch_quarantine_end - __hotpatch_quarantine_start;
    __hotpatch_slots_quarantine_size = __hotpatch_slots_quarantine_end - __hotpatch_slots_quarantine_end;

    /* Place .hotpatch_code after .hotpatch_slots */
    .hotpatch_code :
    {
        . = ALIGN(32);
        __hotpatch_code_start = .;

        *(.hotpatch_code*);

        . = ALIGN(32);
        __hotpatch_code_end = .;
    } > RAM

    __hotpatch_code_size = __hotpatch_code_end - __hotpatch_code_start;
    __hotpatch_code_load_start = LOADADDR(.hotpatch_code);

    /* Place .ramfunc after .hotpatch_code */
    .ramfunc :
    {
        . = ALIGN(32);
        __ramfunc_start = .;

        KEEP(*(.ramfunc*)); /* Keep all .ramfunc symbols */

        . = ALIGN(32);
        __ramfunc_end = .;
    } > RAM AT > FLASH

    __ramfunc_size = __ramfunc_end - __ramfunc_start;
    __ramfunc_load_start = LOADADDR(.ramfunc);
}
INSERT AFTER .bss;
