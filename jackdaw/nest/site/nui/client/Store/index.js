import { createStore } from 'redux';
import { createReducer } from 'redux-act';
const _ = require('lodash');

import NotificationService from '../Services/NotificationService';

import * as actions from './actions';

const initialState = {
    notification: {
        open: false
    }
}

const callServiceMethod = (state, payload, callback) => {
    var iState = JSON.parse(JSON.stringify(state));
    callback(iState, payload);
    return iState;
}

const primitiveReducer = createReducer({
    [actions.nop]: (state, payload) => callServiceMethod(state, payload, null),
    [actions.notifyUser]: (state, payload) => callServiceMethod(state, payload, NotificationService.notifyUser),
    [actions.closeNotification]: (state, payload) => callServiceMethod(state, payload, NotificationService.closeNotification)
}, initialState);

const Store = createStore(primitiveReducer);
module.exports = Store;
