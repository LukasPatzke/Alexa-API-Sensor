import React from 'react';
import { Navbar, Alignment} from '@blueprintjs/core'
import { EndpointTable } from './components/endpoints'
import { ScheduleTable } from './components/scheduler'
import { FocusStyleManager } from "@blueprintjs/core";
 
FocusStyleManager.onlyShowFocusOnTabs();

class App extends React.Component {
  render() {
    return (
      <div >
        <Navbar className='bp3-dark'>
          <Navbar.Group align={Alignment.LEFT}>
            <Navbar.Heading>Alexa API Sensor</Navbar.Heading>
          </Navbar.Group>
        </Navbar>
        <div className='app-main'>
          <EndpointTable/>
          <ScheduleTable/>
        </div>
      </div>
    );
  }
}

export default App;
