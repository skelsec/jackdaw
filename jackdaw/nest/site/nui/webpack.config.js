const webpack = require('webpack');

module.exports = {
    entry: [
        './client/index.js'
    ],
    module: {
      rules: [
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: { presets: [
                "env",
                "react",
                "stage-2"
            ]}
          }
        }, {
          test: /\.scss$/,
          exclude: /node_modules/,
          use: ['style-loader', 'css-loader?url=false' , 'sass-loader?sourceMap']
        },{
          test: /\.json$/,
          exclude: /node_modules/,
          use: ['json-loader']
        }
      ]
    },
    resolve: {
      extensions: ['*', '.js', '.jsx']
    },
    output: {
        path: __dirname + '/dist',
        publicPath: '/',
        filename: 'bundle.js'
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin()
    ],
    devServer: {
        contentBase: './dist',
        watchOptions: {
            poll: true,
            ignored: /node_modules/
        }
    }
};

