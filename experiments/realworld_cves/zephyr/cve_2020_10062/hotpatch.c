#include "hotpatch_helper.h"

#include <mqtt_internal.h>

#pragma GCC push_options
#pragma GCC optimize ("Os")
HOTPATCH_FUNCTION_START_NAKED(fixed_header_decode, 0x2, redirect, 0x8) {
	STORE_REGISTERS("r5, r6");
	VAR_REG(buf, "r0", struct buf_ctx*);
	VAR_REG(type_and_flags, "r1", uint8_t *);
	VAR_REG(length, "r2", uint32_t *);

	uint8_t shift = 0U;
	uint8_t bytes = 0U;

	if ((buf->end - buf->cur) < sizeof(uint8_t)) {
		SET_RETURN_VALUE(-EINVAL);

		RESTORE_REGISTERS("r5, r6");
		RESTORE_REGISTERS("r4, pc");
	}

	*type_and_flags = *(buf->cur++);

	*length = 0U;
	do {
		if (bytes >= MQTT_MAX_LENGTH_BYTES) {
			SET_RETURN_VALUE(-EINVAL);
		RESTORE_REGISTERS("r5, r6");
			RESTORE_REGISTERS("r4, pc");
		}

		if (buf->cur >= buf->end) {
			SET_RETURN_VALUE(-EAGAIN);
		RESTORE_REGISTERS("r5, r6");
			RESTORE_REGISTERS("r4, pc");
		}

		*length += ((uint32_t)*(buf->cur) & MQTT_LENGTH_VALUE_MASK)
								<< shift;
		shift += MQTT_LENGTH_SHIFT;
		bytes++;
	} while ((*(buf->cur++) & MQTT_LENGTH_CONTINUATION_BIT) != 0U);

	if (*length > MQTT_MAX_PAYLOAD_SIZE) {
		SET_RETURN_VALUE(-EAGAIN);
		RESTORE_REGISTERS("r5, r6");
		RESTORE_REGISTERS("r4, pc");
	}

	SET_RETURN_VALUE(0);
	RESTORE_REGISTERS("r5, r6");
	RESTORE_REGISTERS("r4, pc");
}
#pragma GCC