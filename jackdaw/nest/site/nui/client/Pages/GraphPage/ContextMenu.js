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

export const ContextMenu = ({menu, node, handleContextMenuClick}) => {
    const classes = useStyles()

    const constHvtUrl = `${node.id}/hvt/${node.highvalue ? 'clear' : 'set'}`
    const constOvnedUrl = `${node.id}/owned/${node.highvalue ? 'clear' : 'set'}`

    return (
        <List style={{
            position: 'absolute',
            top: `${menu.top}px`,
            left: `${menu.left}px`
            }}
            className={classes.root}
        >
            <ListItem button onClick={() => handleContextMenuClick(constHvtUrl, true)}>
                <ListItemText primary={node.highvalue ? 'HVT' : 'Set HVT'} />
            </ListItem>
            <Divider className={classes.divider}/>
            <ListItem button onClick={() => handleContextMenuClick(constOvnedUrl)}>
                <ListItemText primary={node.owned ? 'Owned' : 'Set Owned'} />
            </ListItem>
        </List>
    )
}