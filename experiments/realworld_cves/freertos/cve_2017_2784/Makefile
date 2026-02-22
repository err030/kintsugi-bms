PROJECT_NAME     := cve_2017_2784
TARGETS          := nrf52840_xxaa
OUTPUT_DIRECTORY := build

PROJ_DIR := .
HP_PROJ_DIR := ../../../..
SDK_ROOT := $(HP_PROJ_DIR)/external/sdk/nRF5_SDK_17.1.0_ddde560
HP_DIR := $(HP_PROJ_DIR)/kintsugi
PATCH_DIR := $(HP_PROJ_DIR)/hotpatches
RTOS_DIR := $(HP_PROJ_DIR)/external/rtos/amazon-freertos/lib
FRPT_DIR := $(HP_PROJ_DIR)/external/rtos/FreeRTOS/FreeRTOS-Plus/Source/FreeRTOS-Plus-TCP

$(OUTPUT_DIRECTORY)/nrf52840_xxaa.out: \
  LINKER_SCRIPT  := FreeRTOS_gcc_nrf52.ld
# Source files common to all targets
SRC_FILES += \
  $(SDK_ROOT)/modules/nrfx/mdk/gcc_startup_nrf52.S \
  $(SDK_ROOT)/components/libraries/log/src/nrf_log_backend_rtt.c \
  $(SDK_ROOT)/components/libraries/log/src/nrf_log_backend_serial.c \
  $(SDK_ROOT)/components/libraries/log/src/nrf_log_default_backends.c \
  $(SDK_ROOT)/components/libraries/log/src/nrf_log_frontend.c \
  $(SDK_ROOT)/components/libraries/log/src/nrf_log_str_formatter.c \
  $(SDK_ROOT)/components/boards/boards.c \
  $(SDK_ROOT)/components/libraries/util/app_error.c \
  $(SDK_ROOT)/components/libraries/util/app_error_handler_gcc.c \
  $(SDK_ROOT)/components/libraries/util/app_error_weak.c \
  $(SDK_ROOT)/components/libraries/fifo/app_fifo.c \
  $(SDK_ROOT)/components/libraries/uart/app_uart_fifo.c \
  $(SDK_ROOT)/components/libraries/util/app_util_platform.c \
  $(SDK_ROOT)/components/libraries/button/app_button.c \
  $(SDK_ROOT)/components/libraries/util/nrf_assert.c \
  $(SDK_ROOT)/components/libraries/atomic/nrf_atomic.c \
  $(SDK_ROOT)/components/libraries/balloc/nrf_balloc.c \
  $(SDK_ROOT)/external/fprintf/nrf_fprintf.c \
  $(SDK_ROOT)/external/fprintf/nrf_fprintf_format.c \
  $(SDK_ROOT)/components/libraries/memobj/nrf_memobj.c \
  $(SDK_ROOT)/components/libraries/ringbuf/nrf_ringbuf.c \
  $(SDK_ROOT)/components/libraries/strerror/nrf_strerror.c \
  $(SDK_ROOT)/components/libraries/uart/retarget.c \
  $(SDK_ROOT)/integration/nrfx/legacy/nrf_drv_uart.c \
  $(SDK_ROOT)/modules/nrfx/soc/nrfx_atomic.c \
  $(SDK_ROOT)/modules/nrfx/drivers/src/prs/nrfx_prs.c \
  $(SDK_ROOT)/modules/nrfx/drivers/src/nrfx_uart.c \
  $(SDK_ROOT)/modules/nrfx/drivers/src/nrfx_uarte.c \
  $(PROJ_DIR)/src/main.c \
  $(SDK_ROOT)/modules/nrfx/mdk/system_nrf52.c \
  $(SDK_ROOT)/integration/nrfx/legacy/nrf_drv_clock.c \
  $(SDK_ROOT)/components/drivers_nrf/nrf_soc_nosd/nrf_nvic.c \
  $(SDK_ROOT)/components/drivers_nrf/nrf_soc_nosd/nrf_soc.c \
  $(SDK_ROOT)/modules/nrfx/drivers/src/nrfx_clock.c \
  $(SDK_ROOT)/modules/nrfx/drivers/src/nrfx_gpiote.c \

# FreeRTOS
SRC_FILES += \
  $(RTOS_DIR)/FreeRTOS/event_groups.c \
  $(RTOS_DIR)/FreeRTOS/portable/MemMang/heap_4.c \
  $(RTOS_DIR)/FreeRTOS/list.c \
  $(RTOS_DIR)/FreeRTOS/queue.c \
  $(RTOS_DIR)/FreeRTOS/stream_buffer.c \
  $(RTOS_DIR)/FreeRTOS/tasks.c \
  $(RTOS_DIR)/FreeRTOS/timers.c \
  $(SDK_ROOT)/components/libraries/timer/app_timer_freertos.c \
  $(SDK_ROOT)/external/freertos/portable/GCC/nrf52/port.c \
  $(SDK_ROOT)/external/freertos/portable/CMSIS/nrf52/port_cmsis.c \
  $(SDK_ROOT)/external/freertos/portable/CMSIS/nrf52/port_cmsis_systick.c \
  $(RTOS_DIR)/pkcs11/mbedtls/aws_pkcs11_mbedtls.c \

# FreeRTOS + TCP
SRC_FILES += \
  $(FRPT_DIR)/FreeRTOS_ARP.c \
  $(FRPT_DIR)/FreeRTOS_DHCP.c \
  $(FRPT_DIR)/FreeRTOS_DNS.c \
  $(FRPT_DIR)/FreeRTOS_IP.c \
  $(FRPT_DIR)/FreeRTOS_Sockets.c \
  $(FRPT_DIR)/FreeRTOS_Stream_Buffer.c \
  $(FRPT_DIR)/FreeRTOS_TCP_IP.c \
  $(FRPT_DIR)/FreeRTOS_TCP_WIN.c \
  $(FRPT_DIR)/FreeRTOS_UDP_IP.c \
  $(PROJ_DIR)/portable/NetworkInterface/dummy_driver.c \
  $(FRPT_DIR)/portable/NetworkInterface/Common/phyHandling.c \
  $(FRPT_DIR)/portable/BufferManagement/BufferAllocation_2.c \
  
  
# mbedtls
SRC_FILES += \
  $(RTOS_DIR)/third_party/mbedtls/library/aes.c \
  $(RTOS_DIR)/third_party/mbedtls/library/aesni.c \
  $(RTOS_DIR)/third_party/mbedtls/library/arc4.c \
  $(RTOS_DIR)/third_party/mbedtls/library/asn1parse.c \
  $(RTOS_DIR)/third_party/mbedtls/library/asn1write.c \
  $(RTOS_DIR)/third_party/mbedtls/library/base64.c \
  $(RTOS_DIR)/third_party/mbedtls/library/bignum.c \
  $(RTOS_DIR)/third_party/mbedtls/library/blowfish.c \
  $(RTOS_DIR)/third_party/mbedtls/library/camellia.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ccm.c \
  $(RTOS_DIR)/third_party/mbedtls/library/certs.c \
  $(RTOS_DIR)/third_party/mbedtls/library/cipher_wrap.c \
  $(RTOS_DIR)/third_party/mbedtls/library/cipher.c \
  $(RTOS_DIR)/third_party/mbedtls/library/cmac.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ctr_drbg.c \
  $(RTOS_DIR)/third_party/mbedtls/library/debug.c \
  $(RTOS_DIR)/third_party/mbedtls/library/des.c \
  $(RTOS_DIR)/third_party/mbedtls/library/dhm.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ecdh.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ecdsa.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ecjpake.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ecp_curves.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ecp.c \
  $(RTOS_DIR)/third_party/mbedtls/library/entropy_poll.c \
  $(RTOS_DIR)/third_party/mbedtls/library/entropy.c \
  $(RTOS_DIR)/third_party/mbedtls/library/error.c \
  $(RTOS_DIR)/third_party/mbedtls/library/gcm.c \
  $(RTOS_DIR)/third_party/mbedtls/library/havege.c \
  $(RTOS_DIR)/third_party/mbedtls/library/hmac_drbg.c \
  $(RTOS_DIR)/third_party/mbedtls/library/md_wrap.c \
  $(RTOS_DIR)/third_party/mbedtls/library/md.c \
  $(RTOS_DIR)/third_party/mbedtls/library/md2.c \
  $(RTOS_DIR)/third_party/mbedtls/library/md4.c \
  $(RTOS_DIR)/third_party/mbedtls/library/md5.c \
  $(RTOS_DIR)/third_party/mbedtls/library/memory_buffer_alloc.c \
  $(RTOS_DIR)/third_party/mbedtls/library/net_sockets.c \
  $(RTOS_DIR)/third_party/mbedtls/library/oid.c \
  $(RTOS_DIR)/third_party/mbedtls/library/padlock.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pem.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pk_wrap.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pk.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pkcs5.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pkcs12.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pkparse.c \
  $(RTOS_DIR)/third_party/mbedtls/library/pkwrite.c \
  $(RTOS_DIR)/third_party/mbedtls/library/platform.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ripemd160.c \
  $(RTOS_DIR)/third_party/mbedtls/library/rsa_internal.c \
  $(RTOS_DIR)/third_party/mbedtls/library/rsa.c \
  $(RTOS_DIR)/third_party/mbedtls/library/sha1.c \
  $(RTOS_DIR)/third_party/mbedtls/library/sha256.c \
  $(RTOS_DIR)/third_party/mbedtls/library/sha512.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_cache.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_ciphersuites.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_cli.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_cookie.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_srv.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_ticket.c \
  $(RTOS_DIR)/third_party/mbedtls/library/ssl_tls.c \
  $(RTOS_DIR)/third_party/mbedtls/library/threading.c \
  $(RTOS_DIR)/third_party/mbedtls/library/timing.c \
  $(RTOS_DIR)/third_party/mbedtls/library/version_features.c \
  $(RTOS_DIR)/third_party/mbedtls/library/version.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509_create.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509_crl.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509_crt.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509_csr.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509write_crt.c \
  $(RTOS_DIR)/third_party/mbedtls/library/x509write_csr.c \
  $(RTOS_DIR)/third_party/mbedtls/library/xtea.c \
  $(RTOS_DIR)/pkcs11/portable/vendor/board/aws_pkcs11_pal.c \

# Hotpatches
SRC_FILES += \
  $(PATCH_DIR)/freertos/cve_2017_2784.c \

# Include folders common to all targets


# Include folders common to all targets
INC_FOLDERS += \
   $(SDK_ROOT)/components \
  $(SDK_ROOT)/modules/nrfx/mdk \
  $(PROJ_DIR) \
  $(PROJ_DIR)/include \
  $(PROJ_DIR)/include/config \
  $(SDK_ROOT)/components/libraries/timer \
  $(SDK_ROOT)/components/libraries/fifo \
  $(SDK_ROOT)/components/libraries/strerror \
  $(SDK_ROOT)/components/libraries/button \
  $(SDK_ROOT)/components/toolchain/cmsis/include \
  $(SDK_ROOT)/components/libraries/util \
  $(SDK_ROOT)/components/libraries/balloc \
  $(SDK_ROOT)/components/libraries/ringbuf \
  $(SDK_ROOT)/modules/nrfx/hal \
  $(SDK_ROOT)/components/libraries/bsp \
  $(SDK_ROOT)/components/libraries/uart \
  $(SDK_ROOT)/components/libraries/log \
  $(SDK_ROOT)/components/libraries/delay \
  $(SDK_ROOT)/modules/nrfx \
  $(SDK_ROOT)/components/libraries/experimental_section_vars \
  $(SDK_ROOT)/integration/nrfx/legacy \
  $(SDK_ROOT)/components/libraries/delay \
  $(SDK_ROOT)/integration/nrfx \
  $(SDK_ROOT)/components/drivers_nrf/nrf_soc_nosd \
  $(SDK_ROOT)/components/libraries/atomic \
  $(SDK_ROOT)/components/boards \
  $(SDK_ROOT)/components/libraries/memobj \
  $(SDK_ROOT)/modules/nrfx/drivers/include \
  $(SDK_ROOT)/external/fprintf \
  $(SDK_ROOT)/components/libraries/log/src \



# FreeRTOS
INC_FOLDERS += \
  $(RTOS_DIR)/include \
  $(RTOS_DIR)/include/private \
  $(RTOS_DIR)/third_party/pkcs11 \
  $(RTOS_DIR)/third_party/mbedtls/include \
  $(SDK_ROOT)/external/freertos/portable/CMSIS/nrf52 \
  $(SDK_ROOT)/external/freertos/portable/GCC/nrf52 \


# FreeRTOS + TCP
INC_FOLDERS += \
  $(FRPT_DIR)/include \
  $(FRPT_DIR)/portable/Compiler/GCC \
  $(FRPT_DIR)/portable/NetworkInterface/include \

# Hotpatch
INC_FOLDERS += \
  $(PATCH_DIR)/include \

# Libraries common to all targets
LIB_FILES += \

# Optimization flags
OPT = -O3 -g3
# Uncomment the line below to enable link time optimization
#OPT += -flto

# C flags common to all targets
CFLAGS += $(OPT)
CFLAGS += -DBOARD_PCA10056
CFLAGS += -DCONFIG_GPIO_AS_PINRESET
CFLAGS += -DFLOAT_ABI_HARD
CFLAGS += -DFREERTOS
CFLAGS += -DNRF52840_XXAA
CFLAGS += -mcpu=cortex-m4
CFLAGS += -mthumb -mabi=aapcs
CFLAGS += -Wall
CFLAGS += -mfloat-abi=hard -mfpu=fpv4-sp-d16
# keep every function in a separate section, this allows linker to discard unused ones
CFLAGS += -ffunction-sections -fdata-sections -fno-strict-aliasing -fomit-frame-pointer 
CFLAGS += -fno-builtin -fshort-enums
CFLAGS += -Wno-error=implicit-function-declaration


# C++ flags common to all targets
CXXFLAGS += $(OPT)
# Assembler flags common to all targets
ASMFLAGS += -g3
ASMFLAGS += -mcpu=cortex-m4
ASMFLAGS += -mthumb -mabi=aapcs
ASMFLAGS += -mfloat-abi=hard -mfpu=fpv4-sp-d16
ASMFLAGS += -DBOARD_PCA10056
ASMFLAGS += -DCONFIG_GPIO_AS_PINRESET
ASMFLAGS += -DFLOAT_ABI_HARD
ASMFLAGS += -DFREERTOS
ASMFLAGS += -DNRF52840_XXAA

# Linker flags
LDFLAGS += $(OPT)
LDFLAGS += -mthumb -mabi=aapcs -L$(SDK_ROOT)/modules/nrfx/mdk -T$(LINKER_SCRIPT)
LDFLAGS += -mcpu=cortex-m4
LDFLAGS += -mfloat-abi=hard -mfpu=fpv4-sp-d16
# let linker dump unused sections
LDFLAGS += -Wl,--gc-sections
# use newlib in nano version
LDFLAGS += --specs=nano.specs

include ${HP_DIR}/Makefile

nrf52840_xxaa: CFLAGS += -D__HEAP_SIZE=8192
nrf52840_xxaa: CFLAGS += -D__STACK_SIZE=8192
nrf52840_xxaa: ASMFLAGS += -D__HEAP_SIZE=8192
nrf52840_xxaa: ASMFLAGS += -D__STACK_SIZE=8192

# Add standard libraries at the very end of the linker input, after all objects
# that may need symbols provided by these libraries.
LIB_FILES += -lc -lnosys -lm


.PHONY: default help

# Default target - first one defined
default: nrf52840_xxaa

# Print all targets that can be built
help:
	@echo following targets are available:
	@echo		nrf52840_xxaa
	@echo		sdk_config - starting external tool for editing sdk_config.h
	@echo		flash      - flashing binary

TEMPLATE_PATH := $(SDK_ROOT)/components/toolchain/gcc


include $(TEMPLATE_PATH)/Makefile.common

$(foreach target, $(TARGETS), $(call define_target, $(target)))

.PHONY: flash erase

# Flash the program
flash: default
	@echo Flashing: $(OUTPUT_DIRECTORY)/nrf52840_xxaa.hex
	nrfjprog -f nrf52 --program $(OUTPUT_DIRECTORY)/nrf52840_xxaa.hex --sectorerase
	nrfjprog -f nrf52 --reset

erase:
	nrfjprog -f nrf52 --eraseall

SDK_CONFIG_FILE := ../config/sdk_config.h
CMSIS_CONFIG_TOOL := $(SDK_ROOT)/external_tools/cmsisconfig/CMSIS_Configuration_Wizard.jar
sdk_config:
	java -jar $(CMSIS_CONFIG_TOOL) $(SDK_CONFIG_FILE)
