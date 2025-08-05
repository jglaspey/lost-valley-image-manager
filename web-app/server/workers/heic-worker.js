const { parentPort, workerData } = require('worker_threads');
const convert = require('heic-convert');

(async () => {
  try {
    const { inputBuffer } = workerData;
    
    console.log(`Worker: Converting HEIF image (${inputBuffer.length} bytes)`);
    
    const outputBuffer = await convert({
      buffer: inputBuffer,
      format: 'JPEG',
      quality: 0.9
    });
    
    console.log(`Worker: Conversion complete (${outputBuffer.length} bytes)`);
    
    parentPort.postMessage(outputBuffer);
  } catch (error) {
    console.error('Worker: HEIF conversion error:', error.message);
    throw error;
  }
})();