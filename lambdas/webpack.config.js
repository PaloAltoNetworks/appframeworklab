const path = require('path');
const { TsConfigPathsPlugin } = require('awesome-typescript-loader');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');


module.exports = (env, argv) => {
    const BUILD_TARGET = argv.mode === 'development' ? 'devel' : 'dist';

    const plugins = [];
    if (argv.mode === 'development') {
        plugins.push(
            new webpack.BannerPlugin({
                banner: 'require("source-map-support").install();',
                raw: true,
                entryOnly: false 
            })
        );
    }

    return {
        stats: 'minimal',
        context: path.resolve(__dirname, 'src'),
        devtool: argv.mode === 'development' ? 'source-map' : false, // Done via UglifyJS
        target: 'node',
        optimization: {
            minimize: argv.mode !== 'development'
        },
        entry: {
            index: [
                './index.ts'
            ]
        },
        resolve: {
            extensions: ['.ts', '.js'],
            modules: [
                'node_modules'
            ],
            alias: {
                'node-fetch$': "node-fetch/lib/index.js"
                // 'deepmerge': 'deepmerge/dist/cjs.js'
            },
            unsafeCache: true,
            symlinks: false,
            plugins: [
                new TsConfigPathsPlugin()
            ]
        },
        output: {
            path: path.resolve(`./${BUILD_TARGET}`),
            filename: './index.js',
            libraryTarget: 'commonjs2'
        },
        module: {
            rules: [
                {
                    test: /\.ts$/,
                    exclude: /node_modules/,
                    use: [
                        { loader: 'awesome-typescript-loader' }
                    ]
                }
            ]
        },
        plugins: [
            ...plugins
        ]
    };
};
