import React from 'react';
import { Button, HTMLTable, Dialog, Classes, FormGroup, InputGroup, Card, Elevation, H5, Text, Tabs, Tab, TextArea } from '@blueprintjs/core'
import axios from 'axios';

const AXIOS_CONFIG = {
    baseURL: 'http://alexa.pi.lan/scheduler/api', 
  }
  
  
  class ScheduleRow extends React.Component {
    handleClick = () => {
      this.props.onClick(this.props.schedule)
    }
    render() {
      return (
        <tr onClick={this.handleClick}>
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.schedule.name}</span></td>
          <td><span className={this.props.isLoading?'bp3-skeleton':''}>{this.props.schedule.run_date}</span></td>
        </tr>
      )
    }
  }
  
  class DeleteDialog extends React.Component {
    render() {
      return (
        <Dialog 
            title='Delete Schedule'
            isOpen={this.props.isOpen}
            onClose={this.props.onCancel}
            canOutsideClickClose={false}
        >
          <div className={Classes.DIALOG_BODY}>
            <Text>Do you want to delete the schedule?</Text>
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
  
  
  class ScheduleDialog extends React.Component {
    state = {
      isDeleteOpen: false,
      selectedTab: 'input',
    }
  
    getSchedule = () => {
      var schedule = this.props.schedule;
      if (this.state.selectedTab === 'input') {
        schedule['id'] = this.id.value;
        schedule['name'] = this.name.value;
        schedule['run_date'] = this.run_date.value;
        schedule['args'] = [this.args.value];
        schedule['func'] = 'scheduler:trigger_event'
        schedule['trigger'] = 'date'
      } else {
        schedule = JSON.parse(this.code)
      }
      return schedule;
    }
  
    handleUpdate = () => {
      const data = {
        event: {
          schedule: this.getSchedule()
        }
      }
  
      axios.put('/endpoints', data, AXIOS_CONFIG).then(res => {
        console.log(res)
        this.props.onClose()
      })
    }
  
    handleCreate = () => {
      const data = this.getSchedule()
      console.log(data)
      axios.post('/jobs', JSON.stringify(data), AXIOS_CONFIG).then(res => {
        console.log(res)
        this.props.onClose()
      }).catch(reason => {
          console.log(reason)
      })
    }
  
    handleDeleteRequest = () => {
      this.setState({isDeleteOpen: true})
    }
  
    handleDelete = () => {  
      axios.delete('/jobs/' + this.props.schedule.id, AXIOS_CONFIG).then(res => {
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
            title='API Schedule'
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
                    schedule={this.props.schedule} 
                    mode={this.props.mode}
                    inputRef={{
                      id: (input) => this.id = input,
                      name: (input) => this.name = input,
                      run_date: (input) => this.run_date = input,
                      args: (input) => this.args = input
                    }}
                  />}
                />
              <Tab/>
              <Tab
                id='code'
                title='JSON'
                panel={
                  <CodeInput
                    schedule={this.props.schedule}
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
          defaultValue={JSON.stringify(this.props.schedule, null, 2)}
        />
      )
    }
  }
  
  class FormInput extends React.Component {
    render() {
      return (
        <div>
          <FormGroup label="Schedule ID" labelFor='id-input'>
            <InputGroup id='id-input' disabled={this.props.mode==='edit'} inputRef={this.props.inputRef.id} defaultValue={this.props.schedule.id}/>
          </FormGroup>
          <FormGroup label="Name" labelFor='id-name'>
            <InputGroup id='id-name' inputRef={this.props.inputRef.name} defaultValue={this.props.schedule.name}/>
          </FormGroup>
          <FormGroup label="Run Date" labelFor='id-run_date'>
            <InputGroup id='id-run_date' inputRef={this.props.inputRef.run_date} defaultValue={this.props.schedule.run_date}/>
          </FormGroup>
          <FormGroup label="Arguments" labelFor='id-args'>
            <InputGroup id='id-args' inputRef={this.props.inputRef.args} defaultValue={this.props.schedule.args}/>
          </FormGroup>
        </div>
      )
    }
  }
  
 export class ScheduleTable extends React.Component {
    constructor(props) {
      super(props);
      this.state = {
        isDialogOpen: false,
        selectedSchedule: {},
        dialogMode: 'edit',
        schedules: [
          {name: 'xxxxxxxxx', run_date: 'xxxxxxxxxxxxxxxxxxxxxxxxxx'},
          {name: 'xxxxxxxxxxxxxx', run_date: 'xxxxxxxxxxxxxxxxxxx'},
          {name: 'xxxxxx', run_date: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'},
        ],
        isLoading: true,
      };
    }
  
    componentDidMount() {
      this.updateData();
    }
  
    updateData = () => {
      this.setState({isLoading: true})
      axios.get('/jobs', AXIOS_CONFIG).then(res => {
        this.setState({
          schedules: res.data,
          isLoading: false,
        })
      })
    }
  
    handleRowClick = (schedule) => {
      this.setState({
        isDialogOpen: true,
        selectedSchedule: schedule,
        dialogMode: 'edit',
      })
    }
  
    handleAdd = () => {
      this.setState({
        isDialogOpen: true,
        selectedSchedule: {},
        dialogMode: 'create',
      })
    }
  
    handleDialogClose = (reload) => {
      this.setState({isDialogOpen: false})
      if (reload) {this.updateData()}
    }
  
    render() {
      const rows = this.state.schedules.map((schedule, index) => {
        return <ScheduleRow key={index} schedule={schedule} onClick={this.handleRowClick} isLoading={this.state.isLoading}/>
      })
      return (
        <Card elevation={Elevation.TWO}>
          <ScheduleDialog 
            isOpen={this.state.isDialogOpen} 
            onClose={()=>this.handleDialogClose(true)}
            onCancel={()=>this.handleDialogClose(false)}
            schedule={this.state.selectedSchedule}
            mode={this.state.dialogMode}
          />
          <H5>API Schedules</H5>
          <HTMLTable interactive={true} className='app-table'>
            <thead>
              <tr>
                <th>Name</th>
                <th>Run Date</th>
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