import React from 'react';
import { Button, HTMLTable, Dialog, Classes, FormGroup, InputGroup, Card, Elevation, H5, Text, Tabs, Tab, TextArea } from '@blueprintjs/core'
import axios from 'axios';

const AXIOS_CONFIG = {
    baseURL: '/api', 
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
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.endpoint.friendlyName}</span></td>
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.endpoint.description}</span></td>
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
      selectedTab: 'input',
    }
  
    getEndpoint = () => {
      var endpoint = this.props.endpoint;
      if (this.state.selectedTab === 'input') {
        if (this.id.value!=='') {endpoint['endpointId'] = this.id.value;}
        endpoint['friendlyName'] = this.name.value;
        endpoint['description'] = this.description.value;
        endpoint['manufacturerName'] = this.manufacturer.value;
      } else {
        endpoint = JSON.parse(this.code)
      }
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
  
    handleTabChange = (newTabId) => {
      this.setState({selectedTab: newTabId})
    }
  
    render() {
      return (
        <Dialog 
            title='API Endpoint'
            isOpen={this.props.isOpen}
            onClose={this.props.onCancel}
            canOutsideClickClose={false}
            className='app-edit-dialog'
        >
          <DeleteDialog
            isOpen={this.state.isDeleteOpen}
            onCancel={()=>this.setState({isDeleteOpen: false})}
            onDelete={this.handleDelete}
          />
          <div className={Classes.DIALOG_BODY}>
            <Tabs id="DialogTabs" onChange={this.handleTabChange}>
              <Tab 
                id="input" 
                title='Input' 
                panel={
                  <FormInput 
                    endpoint={this.props.endpoint} 
                    mode={this.props.mode}
                    inputRef={{
                      id: (input) => this.id = input,
                      name: (input) => this.name = input,
                      description: (input) => this.description = input,
                      manufacturer: (input) => this.manufacturer = input
                    }}
                  />}
                />
              <Tab/>
              <Tab
                id='code'
                title='JSON'
                panel={
                  <CodeInput
                    endpoint={this.props.endpoint}
                    inputRef={(input) => this.code = input}
                  />
                }
              />
            </Tabs>
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            {this.props.mode==='edit'?
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={this.handleDeleteRequest} intent='danger'>Delete</Button>
              <Button onClick={this.handleUpdate} intent='primary'>Save</Button>
              <Button onClick={this.props.onCancel}>Close</Button>
            </div>:
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={this.handleCreate} intent='primary'>Create</Button>
              <Button onClick={this.props.onCancel}>Close</Button>
            </div>
            }
          </div>
        </Dialog>
      )
    }
  }
  
  class CodeInput extends React.Component {
    render() {
      return (
        <TextArea 
          fill={true} 
          inputRef={this.props.inputRef}
          className='app-code-input bp3-code-block'
          defaultValue={JSON.stringify(this.props.endpoint, null, 2)}
        />
      )
    }
  }
  
  class FormInput extends React.Component {
    render() {
      return (
        <div>
          <FormGroup label="Endpoint ID" labelFor='id-input'>
            <InputGroup id='id-input' disabled={this.props.mode==='edit'} inputRef={this.props.inputRef.id} defaultValue={this.props.endpoint.endpointId}/>
          </FormGroup>
          <FormGroup label="Name" labelFor='id-name'>
            <InputGroup id='id-name' inputRef={this.props.inputRef.name} defaultValue={this.props.endpoint.friendlyName}/>
          </FormGroup>
          <FormGroup label="Description" labelFor='id-description'>
            <InputGroup id='id-description' inputRef={this.props.inputRef.description} defaultValue={this.props.endpoint.description}/>
          </FormGroup>
          <FormGroup label="Manufacturer" labelFor='id-manufacturer'>
            <InputGroup id='id-manufacturer' inputRef={this.props.inputRef.manufacturer} defaultValue={this.props.endpoint.manufacturerName}/>
          </FormGroup>
        </div>
      )
    }
  }
  
 export class EndpointTable extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        isDialogOpen: false,
        selectedEndpoint: {},
        dialogMode: 'edit',
        endpoints: [
          {friendlyName: 'xxxxxxxxx', description: 'xxxxxxxxxxxxxxxxxxxxxxxxxx'},
          {friendlyName: 'xxxxxxxxxxxxxx', description: 'xxxxxxxxxxxxxxxxxxx'},
          {friendlyName: 'xxxxxx', description: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'},
        ],
        isLoading: true,
      };
    }
  
    componentDidMount() {
      this.updateData();
    }
  
    updateData = () => {
      this.setState({isLoading: true})
      axios.get('/endpoints', AXIOS_CONFIG).then(res => {
        this.setState({
          endpoints: res.data.map(loadEndpoint),
          isLoading: false,
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
  
    handleDialogClose = (reload) => {
      this.setState({isDialogOpen: false})
      if (reload) {this.updateData()}
    }
  
    render() {
      const rows = this.state.endpoints.map((endpoint, index) => {
        return <EndpointRow key={index} endpoint={endpoint} onClick={this.handleRowClick} isLoading={this.state.isLoading}/>
      })
      return (
        <Card elevation={Elevation.TWO}>
          <EndpointDialog 
            isOpen={this.state.isDialogOpen} 
            onClose={()=>this.handleDialogClose(true)}
            onCancel={()=>this.handleDialogClose(false)}
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
          <Button onClick={this.handleAdd} intent='primary' icon='add'>Add</Button>
        </Card>
      );
    }
  }