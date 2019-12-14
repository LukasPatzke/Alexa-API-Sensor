import React from 'react';
import { Button, Navbar, Alignment, HTMLTable, Dialog, Classes, FormGroup, InputGroup, Card, Elevation, H5, Text } from '@blueprintjs/core'
import axios from 'axios';

const AXIOS_CONFIG = {
  baseURL: 'http://alexa.pi.lan/api', 
}

const loadEndpoint = (data) => {
  return {
    'endpointId': data['EndpointId'],
    'userId': data['UserId'],
    'friendlyName': data['FriendlyName'],
    'manufacturerName': data['ManufacturerName'],
    'description': data['Description'],
    'displayCategories': JSON.parse(data['DisplayCategories']),
    'capabilities': JSON.parse(data['Capabilities']),
  }
}

class EndpointRow extends React.Component {
  handleClick = () => {
    this.props.onClick(this.props.endpoint)
  }
  render() {
    return (
      <tr onClick={this.handleClick}>
        <td>{this.props.endpoint.friendlyName}</td>
        <td>{this.props.endpoint.description}</td>
      </tr>
    )
  }
}

class DeleteDialog extends React.Component {
  render() {
    return (
      <Dialog 
          title='Delete Endpoint'
          isOpen={this.props.isOpen}
          onClose={this.props.onCancel}
          canOutsideClickClose={false}
      >
        <div className={Classes.DIALOG_BODY}>
          <Text>Do you want to delete the endpoint?</Text>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={this.props.onDelete} intent='danger'>Delete</Button>
            <Button onClick={this.props.onCancel}>Cancel</Button>
          </div>
        </div>
      </Dialog>
    )
  }
}


class EndpointDialog extends React.Component {
  state = {
    isDeleteOpen: false,
  }

  getEndpoint = () => {
    var endpoint = this.props.endpoint;
    endpoint['endpointId'] = this.id.value;
    endpoint['friendlyName'] = this.name.value;
    endpoint['description'] = this.description.value;
    endpoint['manufacturerName'] = this.manufacturer.value;

    return endpoint;
  }

  handleUpdate = () => {
    const data = {
      event: {
        endpoint: this.getEndpoint()
      }
    }

    axios.put('/endpoints', data, AXIOS_CONFIG).then(res => {
      console.log(res)
      this.props.onClose()
    })
  }

  handleCreate = () => {
    const data = {
      event: {
        endpoint: this.getEndpoint()
      }
    }

    axios.post('/endpoints', data, AXIOS_CONFIG).then(res => {
      console.log(res)
      this.props.onClose()
    })
  }

  handleDeleteRequest = () => {
    this.setState({isDeleteOpen: true})
  }

  handleDelete = () => {
    const data = [this.props.endpoint.endpointId]
    // axios.delete does not support parameter data
    const config = {
      baseURL: AXIOS_CONFIG.baseURL,
      data: data,
    }

    axios.delete('/endpoints', config).then(res => {
      console.log(res)
      this.setState({isDeleteOpen: false})
      this.props.onClose()
    })
  }

  render() {
    return (
      <Dialog 
          title='API Endpoint'
          isOpen={this.props.isOpen}
          onClose={this.props.onClose}
          canOutsideClickClose={false}
      >
        <DeleteDialog
          isOpen={this.state.isDeleteOpen}
          onCancel={()=>this.setState({isDeleteOpen: false})}
          onDelete={this.handleDelete}
        />
        <div className={Classes.DIALOG_BODY}>
          <FormGroup label="Endpoint ID" labelFor='id-input'>
            <InputGroup id='id-input' inputRef={(input) => this.id = input} disabled={this.props.mode==='edit'} defaultValue={this.props.endpoint.endpointId}/>
          </FormGroup>
          <FormGroup label="Name" labelFor='id-name'>
            <InputGroup id='id-name' inputRef={(input) => this.name = input} defaultValue={this.props.endpoint.friendlyName}/>
          </FormGroup>
          <FormGroup label="Description" labelFor='id-description'>
            <InputGroup id='id-description' inputRef={(input) => this.description = input} defaultValue={this.props.endpoint.description}/>
          </FormGroup>
          <FormGroup label="Manufacturer" labelFor='id-manufacturer'>
            <InputGroup id='id-manufacturer' inputRef={(input) => this.manufacturer = input} defaultValue={this.props.endpoint.manufacturerName}/>
          </FormGroup>
        </div>
        <div className={Classes.DIALOG_FOOTER}>
          {this.props.mode==='edit'?
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={this.handleDeleteRequest} intent='danger'>Delete</Button>
            <Button onClick={this.handleUpdate} intent='primary'>Save</Button>
            <Button onClick={this.props.onClose}>Close</Button>
          </div>:
          <div className={Classes.DIALOG_FOOTER_ACTIONS}>
            <Button onClick={this.handleCreate} intent='primary'>Create</Button>
            <Button onClick={this.props.onClose}>Close</Button>
          </div>
          }
        </div>
      </Dialog>
    )
  }
}

class EndpointTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isDialogOpen: false,
      selectedEndpoint: {},
      dialogMode: 'edit',
      endpoints: [],
    };
  }

  componentDidMount() {
    this.updateData();
  }

  updateData = () => {
    axios.get('/endpoints', AXIOS_CONFIG).then(res => {
      this.setState({
        endpoints: res.data.map(loadEndpoint)
      })
    })
  }

  handleRowClick = (endpoint) => {
    this.setState({
      isDialogOpen: true,
      selectedEndpoint: endpoint,
      dialogMode: 'edit',
    })
  }

  handleAdd = () => {
    this.setState({
      isDialogOpen: true,
      selectedEndpoint: {},
      dialogMode: 'create',
    })
  }

  handleDialogClose = () => {
    this.setState({isDialogOpen: false})
    this.updateData()
  }

  render() {
    const rows = this.state.endpoints.map((endpoint, index) => {
      return <EndpointRow key={index} endpoint={endpoint} onClick={this.handleRowClick}/>
    })
    return (
      <Card elevation={Elevation.TWO}>
        <EndpointDialog 
          isOpen={this.state.isDialogOpen} 
          onClose={this.handleDialogClose}
          endpoint={this.state.selectedEndpoint}
          mode={this.state.dialogMode}
        />
        <H5>API Endpoints</H5>
        <HTMLTable interactive={true} className='app-table'>
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </HTMLTable>
        <Button onClick={this.handleAdd} intent='primary'>Add</Button>
      </Card>
    );
  }
}

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
        </div>
      </div>
    );
  }
}

export default App;
