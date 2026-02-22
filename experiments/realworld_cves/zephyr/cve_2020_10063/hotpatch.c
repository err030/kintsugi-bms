#include "hotpatch_helper.h"
#include <errno.h>
#include <stdint.h>

#include <zephyr/net/net_ip.h>
#include <zephyr/net/net_core.h>
#include <zephyr/net/coap.h>

#pragma GCC push_options
#pragma GCC optimize ("O0")

/*
static int parse_option(uint8_t *data, uint16_t offset, uint16_t *pos,
			uint16_t max_len, uint16_t *opt_delta, uint16_t *opt_len,
			struct coap_option *option)
*/
HOTPATCH_FUNCTION_START(parse_option, 0, redirect, 8) {

	STORE_REGISTERS("r4-r9, sl, fp, lr");
	VAR_REG(data, "r0", uint8_t*);
	VAR_REG(offset, "r1", uint16_t);
	VAR_REG(pos, "r2", uint16_t*);
	VAR_REG(max_len, "r3", uint16_t);
	VAR_REG(opt_len, "r7", uint16_t *);
	VAR_REG(opt_delta, "sl", uint16_t *);
	VAR_REG(option, "r9", struct coap_option *);
	
	__asm__ volatile("ldrd	sl, r7, [sp, #64]\r\n");
	__asm__ volatile("ldr	r9, [sp, #72]\r\n");

	uint16_t hdr_len;
	uint16_t delta;
	uint16_t len;
	uint8_t opt;
	uint16_t t, c;

	int r;

	/*
	static int read_u8(uint8_t *data, uint16_t offset, uint16_t *pos,
		   uint16_t max_len, uint8_t *value)
{
	if (max_len - offset < 1) {
		return -EINVAL;
	}

	*value = data[offset++];
	*pos = offset;

	return max_len - offset;
	*/

	if (max_len - offset < 1) {
		r = -EINVAL;
	}
	else
	{
		opt = data[offset];
		*pos = offset + 1;
		r = max_len - offset + 1;
	}

	if (r < 0) {
		SET_RETURN_VALUE(r);
		RESTORE_REGISTERS("r4-r9, sl, fp, lr");
	}

	/* This indicates that options have ended */
	if (opt == 0xFF) {
		/* packet w/ marker but no payload is malformed */
		if (r > 0) {
			SET_RETURN_VALUE(0);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
		else {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
	}

	*opt_len += 1U;

	delta = (opt & 0xF0) >> 4;
	len = opt & 0x0F;

	/* r == 0 means no more data to read from fragment, but delta
	 * field shows that packet should contain more data, it must
	 * be a malformed packet.
	 */
	if (r == 0 && delta > 12) {
		SET_RETURN_VALUE(-EINVAL);
		RESTORE_REGISTERS("r4-r9, sl, fp, lr");
	}

	if (delta > 12) {
		/* In case 'delta' doesn't fit the option fixed header. */
		r = decode_delta(data, *pos, pos, max_len,
				 delta, &delta, &hdr_len);
		if ((r < 0) || (r == 0 && len > 12)) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
		t = *opt_len;
		c = t + hdr_len;
		*opt_len = c;
		if (c < t) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
	}

	if (len > 12) {
		/* In case 'len' doesn't fit the option fixed header. */
		r = decode_delta(data, *pos, pos, max_len,
				 len, &len, &hdr_len);
		if (r < 0) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}

		t = *opt_len;
		c = t + hdr_len;
		*opt_len = c;
		if (c < t) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
	}

	t = *opt_delta;
	c = t + delta;
	*opt_delta = c;
	if (c < t) {
		SET_RETURN_VALUE(-EINVAL);
		RESTORE_REGISTERS("r4-r9, sl, fp, lr");
	}

	t = *opt_len;
	c = t + len;
	*opt_len = c;
	if (c < t) {
		SET_RETURN_VALUE(-EINVAL);
		RESTORE_REGISTERS("r4-r9, sl, fp, lr");
	}

	/*if (u16_add_overflow(*opt_delta, delta, opt_delta) ||
	    u16_add_overflow(*opt_len, len, opt_len)) {
		return -EINVAL;
	}*/

	if (r == 0 && len != 0U) {
		/* r == 0 means no more data to read from fragment, but len
		 * field shows that packet should contain more data, it must
		 * be a malformed packet.
		 */
		SET_RETURN_VALUE(-EINVAL);
		RESTORE_REGISTERS("r4-r9, sl, fp, lr");
	}

	if (option) {
		/*
		 * Make sure the option data will fit into the value field of
		 * coap_option.
		 * NOTE: To expand the size of the value field set:
		 * CONFIG_COAP_EXTENDED_OPTIONS_LEN=y
		 * CONFIG_COAP_EXTENDED_OPTIONS_LEN_VALUE=<size>
		 */
		if (len > sizeof(option->value)) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}

		option->delta = *opt_delta;
		option->len = len;
		/*
		static int read(uint8_t *data, uint16_t offset, uint16_t *pos,
		uint16_t max_len, uint16_t len, uint8_t *value)
{
	if (max_len - offset < len) {
		return -EINVAL;
	}

	memcpy(value, data + offset, len);
	offset += len;
	*pos = offset;

	return max_len - offset;
}
		*/
		if (max_len - *pos < len) {
			r = -EINVAL;
		}
		else {
			memcpy(&option->value[0], data + *pos, len);
			t = *pos;
			*pos = offset + len;
			r = max_len - t;	
		}
		if (r < 0) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}
	} else {
		t = *pos;
		c = t + len;
		*pos = c;
		if (c < t) {
			SET_RETURN_VALUE(-EINVAL);
			RESTORE_REGISTERS("r4-r9, sl, fp, lr");
		}

		r = max_len - *pos;
	}

	SET_RETURN_VALUE(r);
	RESTORE_REGISTERS("r4-r9, sl, fp, lr");
}
#pragma GCC