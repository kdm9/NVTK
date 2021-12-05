const path = require('path');
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  mode: 'development',
  entry: {
      "imagesort": './src/imagesort.js',
  },
  output: {
    path: path.resolve(__dirname, 'static'),
    filename: '[name].js',
  },
  experiments: {
    asyncWebAssembly: true,
    syncWebAssembly: true,
    topLevelAwait: true
  },
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  plugins: [
    new CopyPlugin({
      patterns: [
        { context: './src/static', from: "*", to: "", toType: "dir"},
      ],
    }),
  ],
};
