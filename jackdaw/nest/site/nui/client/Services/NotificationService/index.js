'use strict';

function NotificationServiceImpl() {

    var state = {
        open: false,
        severity: 'info',
        message: null
    }

    const getState = () => {
        return state;
    }

    const notifyUser = (state, payload) => {
        state.notification.open = true;
        state.notification.severity = payload.severity;
        state.notification.message = payload.message;
        return state;
    }

    const closeNotification = (state, payload) => {
        state.notification.open = false;
        state.notification.severity = 'info';
        state.notification.message = null;
        return state;
    }

    return Object.freeze({
        getState,
        notifyUser,
        closeNotification
    });
}

const NotificationService = NotificationServiceImpl();
export default NotificationService;
