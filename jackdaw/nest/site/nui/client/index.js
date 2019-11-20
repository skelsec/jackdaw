import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { darkBlack } from '@material-ui/core/colors';
import { createMuiTheme, MuiThemeProvider } from '@material-ui/core/styles';

import Store from './Store';
import Main from './Pages/Main';

import './Style/main.scss';
import './Style/boxes.scss';
import './Style/buttons.scss';

const muiTheme = createMuiTheme({
    palette: {
        type: 'dark',
        primary: {
            main: '#c62828'
        },
        secondary: {
            main: '#c62828',
            contrastText: "#fafafa"
        },
        background: {
            default: '#333333',
            paper: 'rgb(27, 28, 29)'
        },
        textColor: '#fafafa',
        primary1Color: '#fafafa',
        primary2Color: '#c62828',
        accent1Color: '#c62828',
        alternateTextColor: '#fafafa'
    },
    appBar: {
        height: 60
    },
    typography: {
        useNextVariants: true,
        fontFamily: [
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif'
        ].join(','),
      },
    overrides: {
        MuiCheckbox: {
            colorSecondary: {
                color: '#777777',
                '&$checked': {
                    color: '#777777',
                },
            },
        },
    }
});

ReactDOM.render(
    <Provider store={Store}>
        <MuiThemeProvider theme={muiTheme}>
            <Main />
        </MuiThemeProvider>
    </Provider>,
  document.getElementById('app')
);
