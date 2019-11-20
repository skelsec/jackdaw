import { createAction } from 'redux-act';

export const nop = createAction('No operation');
export const notifyUser = createAction('show notification to user');
export const closeNotification = createAction('close notification');
