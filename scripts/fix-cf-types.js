import fs from 'fs';

const filePath = 'worker-configuration.d.ts';

try {
  let content = fs.readFileSync(filePath, 'utf-8');
  const targetStr = 'rgb or hex representation of the color you wish to trim (todo: verify the rgba bit)';
  const replacementStr = 'rgb, rgba, or hex representation of the color you wish to trim';

  if (content.includes(targetStr)) {
    content = content.replace(targetStr, replacementStr);
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`Successfully updated ${filePath}`);
  } else {
    console.log(`Target string not found in ${filePath}`);
  }
} catch (error) {
  console.error(`Error processing ${filePath}:`, error.message);
}
