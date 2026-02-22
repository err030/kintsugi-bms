# Hotpatch Generator for Kintsugi

This part of the repository contains the hotpatch generator that we used to obtain the bytes for a hotaptch that is compiled together with Kintsugi.
The idea of this generator is as follows:
We incorporate a "hotpatch" C-File into the build process of Kintsugi and claim that it is used, which it is not. Upon compilation an object-file of the hotpatch code will be generated from which the Hotpatch Generator will take all the necessary information together with the ELF binary generated from the compilation process. Subsequently the Hotpatch Generator produces a valid hotpatch that is in accordance with how Kintsugi hotpatches are expected to look like. Finally, the Hotpatch Generator stores the hotpatch as a byte-array in a header file of the corresponding target firmware. Compiling the firmware again will include the dedicated hotpatch byte array which Kintsugi can use to apply the hotpatch.

*Note that this is not a major contribution of the paper but merely a tool to ease the evaluation process.*