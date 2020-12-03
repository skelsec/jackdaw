import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import React from 'react';
import Divider from '@material-ui/core/Divider';

import { createStyles, makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles(() =>
  createStyles({
    root: {
        color: '#212121',
        backgroundColor: '#FFF',
        border: '1px solid #bdbdbd'
    },
    divider: {
        backgroundColor: '#bdbdbd'
    }
  }),
);

export const ContextMenu = ({menu}) => {
    const classes = useStyles()

    return (
        <List style={{
            position: 'absolute',
            top: `${menu.top}px`,
            left: `${menu.left}px`
            }}
            className={classes.root}
        >
            <ListItem button>
                <ListItemText primary="HVT" />
            </ListItem>
            <Divider className={classes.divider}/>
            <ListItem button>
                <ListItemText primary="Owned" />
            </ListItem>
        </List>
    )
}