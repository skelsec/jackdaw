'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { BrowserHistory, BrowserRouter, Route } from 'react-router-dom';
import classNames from 'classnames';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';

import {
    AppBar, Drawer, IconButton, List,
    ListItem, ListItemIcon, ListItemText, Toolbar
} from '@material-ui/core';

import MenuIcon from '@material-ui/icons/Menu';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import Business from '@material-ui/icons/Business';
import BubbleChart from '@material-ui/icons/BubbleChart';
import ReportProblem from '@material-ui/icons/ReportProblem';
import Search from '@material-ui/icons/Search';

import ApiClient from '../../Components/ApiClient';
import Notification from '../../Components/Notification';

import Domain from '../Domain';
import Anomalies from '../Anomalies';
import GraphPage from '../GraphPage';
import Scan from '../Scan';

const drawerWidth = 240;

const styles = theme => ({
    root: {
        flexGrow: 1,
        zIndex: 1,
        overflow: 'hidden',
        position: 'relative',
        display: 'flex',
        minHeight: '100vh'
    },
    appBar: {
        zIndex: theme.zIndex.drawer + 1,
        transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
        }),
    },
    appBarShift: {
        marginLeft: drawerWidth,
        width: `calc(100% - ${drawerWidth}px)`,
        transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
        }),
    },
    grow: {
        flexGrow: 1,
    },
    menuButton: {
        marginLeft: 12,
        marginRight: 36,
    },
    hide: {
        display: 'none',
    },
    drawerPaper: {
        position: 'relative',
        whiteSpace: 'nowrap',
        width: drawerWidth,
        transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
        })
    },
    drawerPaperClose: {
        overflowX: 'hidden',
        transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
        }),
        width: theme.spacing(7),
        [theme.breakpoints.up('sm')]: {
            width: theme.spacing(9),
        }
    },
    toolbar: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        padding: '0 8px',
        ...theme.mixins.toolbar
    },
    content: {
        flexGrow: 1,
        backgroundColor: theme.palette.background.default
    },
    activeMenu: {
        backgroundColor: theme.palette.background.default,
        color: theme.palette.color
    },
    sectionDesktop: {
        display: 'none',
        [theme.breakpoints.up('md')]: {
          display: 'flex',
        },
    }
});

class MainComponent extends ApiClient {

    state = {
        open: false,
        activeMenu: null
    };

    navigateTo = (history, path, id) => {
        this.setState({ activeMenu: id }, () => {
            history.push(path);
        });
    }

    isActivePage = (id) => {
        const { classes } = this.props;

        if (this.state.activeMenu == id) {
            return classes.activeMenu;
        }
        return null;
    }

    renderPrimaryMenu = () => {
        return (
            <div>
                    <Route render={({ history }) => (
                        <ListItem button
                            className={this.isActivePage(1)}
                            onClick={ () => this.navigateTo(history, '/nest/domain', 1) }
                        >
                            <ListItemIcon>
                                <Business />
                            </ListItemIcon>
                            <ListItemText primary="Domain" />
                        </ListItem>
                    )} />
                    <Route render={({ history }) => (
                        <ListItem button
                            className={this.isActivePage(2)}
                            onClick={ () => this.navigateTo(history, '/nest/anomalies', 2) }
                        >
                            <ListItemIcon>
                                <ReportProblem />
                            </ListItemIcon>
                            <ListItemText primary="Anomalies" />
                        </ListItem>
                    )} />
                    <Route render={({ history }) => (
                        <ListItem button
                            className={this.isActivePage(3)}
                            onClick={ () => this.navigateTo(history, '/nest/graph', 3) }
                        >
                            <ListItemIcon>
                                <BubbleChart />
                            </ListItemIcon>
                            <ListItemText primary="Graph" />
                        </ListItem>
                    )} />
                    <Route render={({ history }) => (
                        <ListItem button
                            className={this.isActivePage(4)}
                            onClick={ () => this.navigateTo(history, '/nest/scan', 4) }
                        >
                            <ListItemIcon>
                                <Search />
                            </ListItemIcon>
                            <ListItemText primary="Scan" />
                        </ListItem>
                    )} />
            </div>
        );
    }

    render() {
        const { classes, theme } = this.props;

        return (
            <BrowserRouter history={BrowserHistory}>
                <div className={classes.root}>
                    <AppBar
                        position="absolute"
                        className={classNames("appbar", classes.appBar, this.state.open && classes.appBarShift)}
                    >
                        <Toolbar disableGutters={!this.state.open}>
                            <IconButton
                                color="primary"
                                aria-label="Open drawer"
                                onClick={(e) => this.setState({ open: true })}
                                className={classNames(classes.menuButton, this.state.open && classes.hide)}
                            >
                                <MenuIcon />
                            </IconButton>
                            <span className="logo-container">
                                <img src="/nest/logo.png" className="logo" />
                            </span>
                            <div className={classes.grow} />
                            <div className={classes.sectionDesktop}>
                            </div>
                        </Toolbar>
                    </AppBar>
                    <Drawer className="drawer"
                        variant="permanent"
                        classes={{
                            paper: classNames(classes.drawerPaper, !this.state.open && classes.drawerPaperClose),
                        }}
                        open={this.state.open}
                    >
                        <div className={classes.toolbar}>
                            <IconButton onClick={(e) => this.setState({ open: false })}>
                                {theme.direction === 'rtl' ? <ChevronRightIcon /> : <ChevronLeftIcon />}
                            </IconButton>
                        </div>
                        <List className="drawer-items">{this.renderPrimaryMenu()}</List>
                    </Drawer>
                    <main className={classes.content}>
                        <div className={classes.toolbar} />
                        <Route exact path="/" component={GraphPage}/>
                        <Route exact path="/nest/domain" component={Domain} />
                        <Route exact path="/nest/anomalies" component={Anomalies} />
                        <Route exact path="/nest/graph" component={GraphPage} />
                        <Route exact path="/nest/scan" component={Scan} />
                    </main>
                <Notification />
                </div>
            </BrowserRouter>
        );
    }
}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {}
}

const Main = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(MainComponent));
export default Main;
