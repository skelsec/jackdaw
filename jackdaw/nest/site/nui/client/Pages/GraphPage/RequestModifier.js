import React, { useState, useEffect } from 'react'
import Accordion from '@material-ui/core/Accordion'
import AccordionSummary from '@material-ui/core/AccordionSummary'
import AccordionDetails from '@material-ui/core/AccordionDetails'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'
import Typography from '@material-ui/core/Typography';
import { FormControlLabel, FormGroup, Switch } from '@material-ui/core';

export const RequestModifier = ({onChange}) => {
    const [state, setstate] = useState({
        Owner: true,
        allowedtoact: true,
        gplink: true,
        pwsharing: true,
        psremote: true,
        adminTo: true,
        executeDCOM: true,
        canRDP: true,
        hasSession: true,
        GenericWrite: true,
        sqladmin: true,
        trustedBy: true,
        unknown: true,
        WriteOwner: true,
        ['User-Force-Change-Password']: true,
        GetChanges: true,
        GetChangesALL: true,
        ExtendedAll: true,
        ExtendedRightALL: true,
        AddMember: true,
        GenericALL: true,
        WriteDacl: true,
    })

    useEffect(() => {
        let tempArray = []
        Object.keys(state).map(el => {
            if(!state[el]) {
                tempArray.push(el)
            }
        })
        onChange(tempArray)
    }, [state])

    return (
        <Accordion>
            <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="panel1a-content"
            id="panel1a-header"
            >
                <Typography>Request modifiers</Typography>
            </AccordionSummary>
            <AccordionDetails>
                <FormGroup>
                    {Object.keys(state).map(el => (
                        <FormControlLabel
                            key={el}
                            control={
                                <Switch
                                checked={state[el]}
                                onChange={() => setstate((prevState) => ({
                                    ...state,
                                    [el]: !prevState[el]
                                }))}
                                value={el}
                            />
                            }
                            label={el}
                        />
                    ))}
                </FormGroup>
            </AccordionDetails>
        </Accordion>
    )

}