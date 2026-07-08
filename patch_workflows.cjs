const fs = require('fs');

const file1 = '.github/workflows/deploy-preview.yml';
let content1 = fs.readFileSync(file1, 'utf8');

// Convert `apiToken` to `env: CLOUDFLARE_API_TOKEN` block
content1 = content1.replace(
  /apiToken:\s*\$\{\{\s*secrets\.CLOUDFLARE_API_TOKEN\s*\}\}/g,
  ''
);

// We need to find the `uses: cloudflare/wrangler-action...` block and append the `env` var to it.
content1 = content1.replace(
  /command:\s*deploy\s*--env=""\n/g,
  'command: deploy --env=""\n        env:\n          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}\n'
);

fs.writeFileSync(file1, content1);

const file2 = '.github/workflows/deploy-production.yml';
let content2 = fs.readFileSync(file2, 'utf8');

content2 = content2.replace(
  /apiToken:\s*\$\{\{\s*secrets\.CLOUDFLARE_API_TOKEN\s*\}\}/g,
  ''
);

content2 = content2.replace(
  /command:\s*deploy\s*--name\s*hsb-boden\s*--var\s*ENVIRONMENT:production\n/g,
  'command: deploy --name hsb-boden --var ENVIRONMENT:production\n        env:\n          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}\n'
);

fs.writeFileSync(file2, content2);
