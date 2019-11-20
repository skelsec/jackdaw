'use strict';

import React from 'react';
import { connect } from 'react-redux';
import { withStyles } from '@material-ui/core/styles';
import { Box, VBox } from 'react-layout-components';
import { Button, ButtonGroup, Paper, Popper, Grow, MenuList, MenuItem, ClickAwayListener } from '@material-ui/core';

import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown';

const styles = theme => ({
});

const options = [
    { key: null, display: 'Select...' },
    { key: 'machines_description', display: 'Machine Descriptions' },
    { key: 'users_description', display: 'User Account Descriptions' },
    { key: 'machines_domainmismatch', display: 'SMB Domain Mismatches' },
    { key: 'machines_outdatedos', display: 'Outdated Operating Systems' },
    { key: 'machines_smbsign', display: 'SMB Signing Issues' },
    { key: 'machines_users', display: 'User Account Issues' }
];

class SplitButtonComponent extends React.Component {

    state = {
        open: false,
        mode: 'machines_description',
        selectedIndex: 0
    }

    constructor(props) {
        super(props);
        this.anchorRef = React.createRef();
    }

    componentWillReceiveProps(nextProps) {
        if ([undefined, null].includes(nextProps.mode)) return;
        let v = options.map((opt, index) => {
            if (opt.key != nextProps.mode) return;
            return {
                index: index,
                name: opt.display
            };
        });
        v = v.filter(item => item != null)[0];
        this.setState({
            mode: v.name,
            selectedIndex: v.index
        });
    }

    handleClose = (event) => {
        if (this.anchorRef.current && this.anchorRef.current.contains(event.target)) {
            return;
        }
    
        this.setState({ open: false});
    }

    handleToggle = () => {
        this.setState({ open: !this.state.open });
    }

    handleClick = () => {}

    updateMode = (index, mode) => {
        this.setState({ 
            selectedIndex: index,
            open: false
        })
        this.props.update(mode);
    }

    render() {
        return (
            <VBox>
                <ButtonGroup
                    color="primary"
                    ref={ref => {
                        this.anchorRef = ref;
                    }}
                    aria-label="split button"
                >
                    <Button onClick={this.handleClick}>{options[this.state.selectedIndex].display}</Button>
                    <Button
                        color="primary"
                        size="small"
                        aria-owns={this.state.open ? 'menu-list-grow' : undefined}
                        aria-haspopup="true"
                        onClick={this.handleToggle}
                    >
                        <ArrowDropDownIcon />
                    </Button>
                </ButtonGroup>
                <Popper open={this.state.open} anchorEl={this.anchorRef.current} transition disablePortal>
                {({ TransitionProps, placement }) => (
                    <Grow
                        {...TransitionProps}
                        style={{
                            transformOrigin: placement === 'bottom' ? 'center top' : 'center bottom',
                        }}
                    >
                        <Paper id="menu-list-grow">
                            <ClickAwayListener onClickAway={this.handleClose}>
                                <MenuList>
                                    {options.map((option, index) => (
                                        <MenuItem
                                            key={option.key}
                                            selected={index === this.state.selectedIndex}
                                            onClick={event => this.updateMode(index, option.key) }
                                        >
                                            {option.display}
                                        </MenuItem>
                                    ))}
                                </MenuList>
                            </ClickAwayListener>
                        </Paper>
                    </Grow>
                )}
                </Popper>
            </VBox>
        );
    }

}

const mapStateToProps = (state) => {
    return {}
}

const mapDispatchToProps = (dispatch) => {
    return {}
}

const SplitButton = connect(mapStateToProps, mapDispatchToProps)(withStyles(styles, { withTheme: true })(SplitButtonComponent));
export default SplitButton;
