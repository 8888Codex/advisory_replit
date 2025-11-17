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
            // Retornar um stub que não tenta importar nada
            return { path: '', namespace: 'vite-stub' };
          });
          
          build.onResolve({ filter: /^\.\/vite\.ts$/ }, () => {
            return { path: '', namespace: 'vite-stub' };
          });
          
          build.onResolve({ filter: /vite\.config/ }, () => {
            return { external: true, sideEffects: false };
          });
          
          // Stub para o namespace vite-stub - retorna um módulo vazio
          // O tree-shaking vai remover o código que usa este módulo
          build.onLoad({ filter: /.*/, namespace: 'vite-stub' }, () => {
            return {
              contents: `
                // Stub vazio para produção - código de desenvolvimento será removido pelo tree-shaking
                export const setupVite = async () => {
                  // Este código nunca será executado em produção
                  // porque o tree-shaking remove o bloco else que o chama
                };
              `,
              loader: 'js',
            };
          });
        }
      },
    },
  ],
  // Definir NODE_ENV para tree-shaking e minificação
  // Isso permite que o esbuild remova código morto baseado em condições
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
  },
  // Garantir que condições baseadas em NODE_ENV sejam otimizadas
  conditions: ['production', 'node'],
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

