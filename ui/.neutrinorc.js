const DEFAULT_HOST = 'localhost';
const DEFAULT_PORT = 3000;
const port = process.env.PORT || DEFAULT_PORT;
const REACT_APP_COLLECTION_URL = process.env.REACT_APP_COLLECTION_URL || 'http://localhost:8000/api'

module.exports = {
  options: {
    root: __dirname,
  },
  use: [
    [
      '@neutrinojs/react',
      {
        devServer: {
          host: process.env.HOST || DEFAULT_HOST,
          port,
          historyApiFallback: {
            disableDotRule: true,
          },
          headers: {
            'Content-Security-Policy': "TODO",
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'no-referrer',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; always;',
          },
        },
        env: {
          HOST: DEFAULT_HOST,
          PORT: DEFAULT_PORT,
          REACT_APP_COLLECTION_URL,
        },
      }
    ],
    (neutrino) => {
      neutrino.config.resolve.alias
        .set('react-dom', '@hot-loader/react-dom');

      neutrino.config.output.set('globalObject', 'this');
    },
    '@neutrinojs/jest',
  ]
};
