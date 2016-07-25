/**
 * @license
 * Copyright 2016 Cluster Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var object = skit.platform.object;
var util = skit.platform.util;

var LKConfigAPIClient = library.api.LKConfigAPIClient;
var SettingRules = library.react.config.SettingRules;
var Select = library.react.components.Select;
var shallowequal = library.react.lib.shallowequal;
var FormatCodeSample = library.react.config.codeformatting;


var validate = {
  isValidRule: function(rule) {
    if (!rule.key || !rule.kind) {
      return false;
    }

    return LKConfigAPIClient.isValidValue(rule.kind, rule.value);
  }
};


var CreateNewSetting = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  getInitialState: function() {
    return {
      key: '',
      kind: 'string',
      value: '',
      description: '',
      bundleId: this.props.bundleId || '',
      error: null,
      addNew: false
    };
  },

  handleError: function(msg) {
    this.setState({error: msg});
  },

  componentWillUpdate: function(nextProps, nextState) {
    if (this.state.kind != nextState.kind) {
      nextState.value = '';
    }
  },

  createRule: function() {
    var keyExists = this.props.settings.find(function(setting){
      if (setting.key == this.state.key) {
        this.handleError('You already have a setting with this key.');
        this.refs.key.focus();
        return true;
      }
    }, this);

    if (keyExists) {
      return false;
    }

    var params = object.copy(this.state);
    LKConfigAPIClient.createRule(params, {
      onSuccess: function(newSetting) {
        // NOTE: Need to use "newSetting" here because it has the ID set.
        // Top-level settings get a "rules" array for their sub-rules.
        newSetting.rules = [];
        this.props.addNewSetting(newSetting);
        this.setState(this.getInitialState());
      },
      context: this
    });
  },

  toggleNew: function() {
    this.setState({addNew: !this.state.addNew});
  },

  render: function() {
    return (
      <li className="row inspector-expandable-row add-new">

        {
          (!this.state.addNew) ?
            <div onClick={this.toggleNew} className="add-new-trigger">
              <div className="col-sm-1">
                <i className="fa fa-plus"></i>
              </div>
              <div className="col-sm-10">
                <div className="inspector-expandable-row-text">Add New Feature</div>
              </div>
            </div>
            :

            <div>
              <div className="col-sm-12">
                <div className="expanded-light-box form">
                  <div className="row">

                    <div className="col-xs-12">
                      <label className="control-label">Add New Key</label>
                    </div>

                    {(this.state.error) ?
                      <div className="col-xs-12 error">
                        <p className="bg-danger">{this.state.error}</p>
                      </div>
                      :
                      null
                    }

                    <div className="col-sm-4 form-group">
                      <label className="above-field">Key</label>
                      <input type="text" ref="key" className="form-control" placeholder="enableFeature" valueLink={this.linkState('key')}/>
                    </div>

                    <div className="col-xs-3 form-group">
                      <label className="above-field">Type</label>
                      <Select
                        valueLink={this.linkState('kind')}
                        options={[
                          {value:'string', label:'string'},
                          {value:'bool', label:'bool'},
                          {value:'int', label:'int'},
                          {value:'float', label:'float'}
                        ]} />
                    </div>

                    <div className="col-xs-5 form-group">
                      <label className="above-field">Default Value</label>
                      {(this.state.kind == 'bool') ?
                        <Select
                          valueLink={this.linkState('value')}
                          options={[
                            {value:'', label:'Select a value'},
                            {value:false, label:'False'},
                            {value:true, label:'True'}
                          ]} />
                        :
                        <input type="text" ref="value" className="form-control" placeholder="What is the default value?" valueLink={this.linkState('value')}/>
                      }
                    </div>

                    <div className="col-xs-12 form-group">
                      <label className="above-field">Description</label>
                      <input type="text" name="description" placeholder="What does this key do?" className="form-control" valueLink={this.linkState('description')}/>
                    </div>

                    <div className="col-xs-12 form-group">
                      {!validate.isValidRule(this.state) ?
                        <button className="btn btn-primary" disabled><i className="fa fa-plus"></i> Add Key</button>
                        :
                        <button className="btn btn-primary" onClick={this.createRule}><i className="fa fa-plus"></i> Add Key</button>
                      }
                    </div>
                  </div>
                </div>
              </div>
            </div>
        }

      </li>
    )
  }
});


var Setting = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  componentWillReceiveProps: function(nextProps) {
    var next = nextProps.setting;
    // When a key is deleted from the parent, the changes propogate down
    // if the id doesn't match a key was deleted so update the state to rerender the component
    if (this.state.id != next.id) {
      next.editmode = false;
      this.setState(next);
    }

  },

  getInitialState: function() {
    return this.props.setting || {};
  },

  componentDidUpdate: function(prevProps, prevState) {
    this.updateKey(prevState, this.state);
  },

  handleError: function(msg) {

  },

  updateKey: function(prevState, currentState) {
    var oldSetting = object.copy(prevState);
    var setting = object.copy(currentState);
    delete oldSetting.editmode;
    delete setting.editmode;

    // Only send an update for the key if the key's id is the same and it has changes
    if ((setting.id == oldSetting.id) && !shallowequal(setting, oldSetting)) {
      if (this.timer) {
        clearTimeout(this.timer);
      }

      this.timer = util.setTimeout(function() {
        this.reallyUpdateKey(setting);
      }, 350, this);
    }
  },

  reallyUpdateKey: function(setting) {
    LKConfigAPIClient.editRule(setting, {
      onSuccess: function(updatedRule) {
        // Carry over additional sub-rules list from previous.
        updatedRule.rules = setting.rules;

        this.props.setUpdatedKey(updatedRule, this.props.settingIndex);
        this.props.setIsPublished(false);
      },
      onError: function(error, msg) {
        this.handleError(msg);
      },
      context: this
    });
  },

  maybeRemoveKey: function() {
    LKConfigAPIClient.deleteRule(this.state, {
      onSuccess: function(removed) {
        this.props.removeKey();
      },
      onError: function(error, msg) {
        this.handleError(msg);
      },
      context: this
    });
  },

  edit: function(evt) {
    if (evt.target != evt.currentTarget) {
      return;
    }

    this.setState({editmode: !this.state.editmode});
  },

  render: function() {
    return (
      <li className={this.state.editmode ? 'row inspector-expandable-row expanded' : 'row inspector-expandable-row'} onClick={this.edit}>
        <div className="expansion-trigger">
          <div className="col-sm-1">
            <i className="fa fa-code"></i>
          </div>
          <div className="col-sm-5">
            <input type="text" className="form-control" valueLink={this.linkState('key')} disabled/>
          </div>
          <div className="col-sm-5">
            {(this.state.kind == 'bool') ?
              <Select
                valueLink={this.linkState('value')}
                options={[
                  {value:false, label:'False'},
                  {value:true, label:'True'}
                ]} />
              :
              <input type="text" name="app_name" className="form-control" placeholder="What is the default value?" valueLink={this.linkState('value')}/>
            }
          </div>
        </div>

        {(this.state.editmode) ?
          <div className="expanded-container">
            <div className="col-sm-9">
              <label className="above-field">Description</label>
              <div className="setting-description">
                <input type="text" name="description" placeholder="What does this key do?" className="form-control" valueLink={this.linkState('description')}/>
              </div>
            </div>
            <div className="col-sm-3">
              <label className="above-field">Type</label>
              <input type="text" className="form-control" valueLink={this.linkState('kind')} disabled/>
            </div>

            <div className="col-sm-12">
              <div className="panel-group">
                <SettingRules
                  setting={this.props.setting}
                  setIsPublished={this.props.setIsPublished}
                  setUpdatedKey={this.props.setUpdatedKey}
                  settingIndex={this.props.settingIndex} />
              </div>
            </div>

            <div className="col-sm-12">
              <div className="setting-integration">
                <label className="above-field">Objective-C</label>
                <code>
                  <FormatCodeSample setting={this.state} lang='obj-c'/>
                </code>
                <label className="above-field">Swift</label>
                <code>
                  <FormatCodeSample setting={this.state} lang='swift'/>
                </code>
              </div>
            </div>

            <button className="btn-link grey-icon remove-setting" disabled={this.props.setting.rules.length} title="Remove overrides first" onClick={this.maybeRemoveKey}>
              <i className="fa fa-trash"></i> Delete
            </button>
          </div>
        :
          null
        }
      </li>
    );
  }
});

var ConfigSettings = React.createClass({
  getInitialState: function() {
    return {
      settings: this.props.settings || []
    }
  },

  render: function() {
    return (
      <div className="editor-workspace">
        <ul className="list-unstyled inspector-list inspector-list-expandable">
          <li className="row inspector-col-labels">
            <div className="col-sm-1">
            </div>
            <div className="col-sm-5">
              <label className="above-field">Key</label>
            </div>
            <div className="col-sm-5">
              <label className="above-field">Default Value</label>
            </div>
          </li>

          {this.props.settings.map(function(setting, i) {
            return (
              <Setting
                setting={setting}
                key={i}
                settingIndex={i}
                setIsPublished={this.props.setIsPublished}
                setUpdatedKey={this.props.setUpdatedKey}
                removeKey={this.props.removeKey.bind(this, i)} />
            )
          }, this)}

          <CreateNewSetting
            settings={this.props.settings}
            addNewSetting={this.props.addNewSetting}
            bundleId={this.props.bundleId} />

        </ul>
      </div>
    );
  }
});

module.exports = ConfigSettings;