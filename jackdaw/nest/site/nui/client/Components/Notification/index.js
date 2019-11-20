import React from 'react';
import clsx from 'clsx';
import { IconButton, Snackbar, SnackbarContent } from '@material-ui/core';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { amber, green } from '@material-ui/core/colors';

import CheckCircleIcon from '@material-ui/icons/CheckCircle';
import InfoIcon from '@material-ui/icons/Info';
import ErrorIcon from '@material-ui/icons/Error';
import WarningIcon from '@material-ui/icons/Warning';
import CloseIcon from '@material-ui/icons/Close';

import * as actions from '../../Store/actions';

const styles = theme => ({
    success: {
        backgroundColor: green[600]
    },
    error: {
        backgroundColor: theme.palette.error.dark
    },
    info: {
        backgroundColor: theme.palette.primary.main
    },
    warning: {
        backgroundColor: amber[700]
    },
    icon: {
        fontSize: 20,
    },
    iconVariant: {
        opacity: 0.9,
        marginRight: theme.spacing(1)
    },
    message: {
        display: 'flex',
        alignItems: 'center'
    }
});

const variantIcon = {
    success: CheckCircleIcon,
    warning: WarningIcon,
    error: ErrorIcon,
    info: InfoIcon
};

class NotificationComponent extends React.Component {

    handleClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        this.props.closeNotification();
    };

    renderContent = () => {
        
        const { classes } = this.props;
        const Icon = variantIcon[this.props.notification.severity];

        return (
            <SnackbarContent
                className={classes[this.props.notification.severity]}
                aria-describedby="client-snackbar"
                message={
                    <span id="client-snackbar" className={classes.message}>
                        <Icon className={clsx(classes.icon, classes.iconVariant)} />
                        {this.props.notification.message}
                    </span>
                }
                action={[
                    <IconButton
                        key="close"
                        aria-label="close"
                        color="inherit"
                        onClick={this.handleClose}
                    >
                        <CloseIcon className={classes.icon} />
                    </IconButton>,
                ]}
            />
        );
    }

    render() {
        return (
            <Snackbar
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'left',
                }}
                open={this.props.notification.open}
                autoHideDuration={4000}
                onClose={this.handleClose}
            >
                {this.renderContent()}
            </Snackbar>
        );
    }
}

const mapStateToProps = (state) => {
    return {
        notification: state.notification
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        closeNotification: (payload) => { dispatch(actions.closeNotification(payload)) }
    }
}

const Notification = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(NotificationComponent));
export default Notification;
