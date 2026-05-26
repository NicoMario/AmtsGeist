const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = (env, argv) => {
  const isDev = argv.mode === "development";
  return {
    devtool: isDev ? "source-map" : false,
    entry: {
      taskpane: "./src/taskpane/taskpane.ts",
    },
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "[name].js",
      clean: true,
    },
    resolve: {
      extensions: [".ts", ".js"],
    },
    module: {
      rules: [
        {
          test: /\.ts$/,
          use: "ts-loader",
          exclude: /node_modules/,
        },
        {
          test: /\.css$/,
          use: ["style-loader", "css-loader"],
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        filename: "taskpane.html",
        template: "./src/taskpane/taskpane.html",
        chunks: ["taskpane"],
      }),
      new CopyWebpackPlugin({
        patterns: [{ from: "assets", to: "assets", noErrorOnMissing: true }],
      }),
    ],
    devServer: {
      static: { directory: path.join(__dirname, "dist") },
      server: "https",
      port: 3000,
      headers: { "Access-Control-Allow-Origin": "*" },
    },
  };
};
