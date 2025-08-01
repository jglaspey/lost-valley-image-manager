const sharp = require('sharp');
const path = require('path');

// Generate a simple placeholder image
async function createPlaceholder(width = 400, height = 300) {
  const svg = `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="#f3f4f6"/>
      <text x="50%" y="45%" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#6b7280">
        Image
      </text>
      <text x="50%" y="60%" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#9ca3af">
        Unavailable
      </text>
    </svg>
  `;
  
  return sharp(Buffer.from(svg))
    .png()
    .toBuffer();
}

module.exports = { createPlaceholder };