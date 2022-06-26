const path = require('path');
const webpack = require('webpack');
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  mode: 'development',
  entry: {
      "imagesort": './src/imagesort.js',
      "labelsheet": './src/labelsheet.js',
      "index": './src/index.js',
      "extra": './src/extra.js',
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
    new webpack.DefinePlugin({
      __VUE_PROD_DEVTOOLS__: true,
    })
  ],
};
