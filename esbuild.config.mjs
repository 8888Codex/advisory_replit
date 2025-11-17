import esbuild from 'esbuild';

const isProduction = process.env.NODE_ENV === 'production';

const buildOptions = {
  entryPoints: ['server/index.ts'],
  platform: 'node',
  bundle: true,
  format: 'esm',
  outdir: 'dist',
  packages: 'external',
  external: [
    // Externalizar todos os pacotes npm (não fazer bundle)
    // Especificamente excluir vite e seus plugins
    'vite',
    '@vitejs/plugin-react',
    '@replit/vite-plugin-runtime-error-modal',
    '@replit/vite-plugin-cartographer',
    '@replit/vite-plugin-dev-banner',
  ],
  plugins: [
    {
      name: 'exclude-vite-files',
      setup(build) {
        // Em produção, marcar vite.ts e vite.config.ts como externos
        // Isso impede que sejam incluídos no bundle
        if (isProduction) {
          build.onResolve({ filter: /^\.\/vite$/ }, () => {
            return { external: true, sideEffects: false };
          });
          
          build.onResolve({ filter: /^\.\/vite\.ts$/ }, () => {
            return { external: true, sideEffects: false };
          });
          
          build.onResolve({ filter: /vite\.config/ }, () => {
            return { external: true, sideEffects: false };
          });
        }
      },
    },
  ],
  // Definir NODE_ENV para tree-shaking e minificação
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
  },
  // Minificar e remover código morto
  minify: true,
  treeShaking: true,
  // Remover código inacessível
  legalComments: 'none',
};

esbuild.build(buildOptions)
  .then(() => {
    console.log('✅ Build concluído com sucesso');
  })
  .catch((error) => {
    console.error('❌ Erro no build:', error);
    process.exit(1);
  });

