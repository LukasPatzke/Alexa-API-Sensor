import React from 'react';
import { Button, HTMLTable, Dialog, Classes, FormGroup, InputGroup, Card, Elevation, H5, Text } from '@blueprintjs/core'
import axios from 'axios';
import moment from 'moment-timezone';

const AXIOS_CONFIG = {
    baseURL: '/store', 
  }
  
  
  class EntryRow extends React.Component {
    handleClick = () => {
      this.props.onClick(this.props.entry)
    }
    render() {
      return (
        <tr onClick={this.handleClick}>
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.entry.key}</span></td>
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.entry.value}</span></td>
        </tr>
      )
    }
  }
  
  class DeleteDialog extends React.Component {
    render() {
      return (
        <Dialog 
            title='Delete entry'
            isOpen={this.props.isOpen}
            onClose={this.props.onCancel}
            canOutsideClickClose={false}
        >
          <div className={Classes.DIALOG_BODY}>
            <Text>Do you want to delete the entry?</Text>
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
  
  
  class EntryDialog extends React.Component {
    state = {
      isDeleteOpen: false,
      selectedTab: 'input',
    }
  
    getentry = () => {
      var entry = this.props.entry;

      entry['key'] = this.key.value;
      entry['value'] = this.value.value;

      return entry;
    }
  
    handleUpdate = () => {
      const entry = this.getentry()
      console.log('update')
      axios.patch('/entry/' + this.props.entry.key, entry, AXIOS_CONFIG).then(res => {
        console.log(res)
        this.props.onClose()
      })
    }

  
    handleDeleteRequest = () => {
      this.setState({isDeleteOpen: true})
    }
  
    handleDelete = () => {  
      axios.delete('/entry/' + this.props.entry.key, AXIOS_CONFIG).then(res => {
        console.log(res)
        this.setState({isDeleteOpen: false})
        this.props.onClose()
      })
    }

  
    render() {
      return (
        <Dialog 
            title='Store Entry'
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
            <FormInput 
              entry={this.props.entry} 
              mode={this.props.mode}
              inputRef={{
                key: (input) => this.key = input,
                value: (input) => this.value = input,
              }}
            />
          </div>
          <div className={Classes.DIALOG_FOOTER}>
            <div className={Classes.DIALOG_FOOTER_ACTIONS}>
              <Button onClick={this.handleDeleteRequest} intent='danger'>Delete</Button>
              <Button onClick={this.handleUpdate} intent='primary'>Save</Button>
              <Button onClick={this.props.onCancel}>Close</Button>
            </div>
          </div>
        </Dialog>
      )
    }
  }

  
  class FormInput extends React.Component {
    formatDate(string) {
      var date = moment.utc(string)
      return date.format('DD.MM.YYYY HH:mm:ss')
    }
    render() {
      return (
        <div>
          <FormGroup label="Key" labelFor='id-key'>
            <InputGroup id='id-key' disabled={true} inputRef={this.props.inputRef.key} defaultValue={this.props.entry.key}/>
          </FormGroup>
          <FormGroup label="Value" labelFor='id-value'>
            <InputGroup id='id-value' inputRef={this.props.inputRef.value} defaultValue={this.props.entry.value}/>
          </FormGroup>
          <FormGroup label="Created">
            <InputGroup disabled={true} defaultValue={this.formatDate(this.props.entry.created)}/>
          </FormGroup>
          <FormGroup label="Last Changed">
            <InputGroup disabled={true} defaultValue={this.formatDate(this.props.entry.last_changed)}/>
          </FormGroup>
          <FormGroup label="Last Accessed">
            <InputGroup disabled={true} defaultValue={this.formatDate(this.props.entry.last_accessed)}/>
          </FormGroup>
        </div>
      )
    }
  }
  
 export class StoreTable extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        isDialogOpen: false,
        selectedEntry: {},
        entries: [
          {key: 'xxxxxxxxx', value: 'xxxxxxxxxxxxxxxxxxxxxxxxxx'},
          {key: 'xxxxxxxxxxxxxx', value: 'xxxxxxxxxxxxxxxxxxx'},
          {key: 'xxxxxx', value: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'},
        ],
        isLoading: true,
      };
    }
  
    componentDidMount() {
      this.updateData();
    }
  
    updateData = () => {
      this.setState({isLoading: true})
      axios.get('/entries', AXIOS_CONFIG).then(res => {
        this.setState({
          entries: res.data,
          isLoading: false,
        })
      })
    }
  
    handleRowClick = (entry) => {
      this.setState({
        isDialogOpen: true,
        selectedEntry: entry,
      })
    }
  
    handleDialogClose = (reload) => {
      this.setState({isDialogOpen: false})
      if (reload) {this.updateData()}
    }
  
    render() {
      const rows = this.state.entries.map((entry, index) => {
        return <EntryRow key={index} entry={entry} onClick={this.handleRowClick} isLoading={this.state.isLoading}/>
      })
      return (
        <Card elevation={Elevation.TWO}>
          <EntryDialog 
            isOpen={this.state.isDialogOpen} 
            onClose={()=>this.handleDialogClose(true)}
            onCancel={()=>this.handleDialogClose(false)}
            entry={this.state.selectedEntry}
          />
          <H5>Store Entries</H5>
          <HTMLTable interactive={true} className='app-table'>
            <thead>
              <tr>
                <th>Key</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </HTMLTable>
        </Card>
      );
    }
  }