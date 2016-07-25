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
var Select = library.react.components.Select;
var shallowequal = library.react.lib.shallowequal;
var update = library.react.lib.update;


var Rule = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  componentWillMount: function() {
  },

  getInitialState: function() {
    return this.props.rule;
  },

  shouldComponentUpdate: function(nextProps, nextState) {
    return !shallowequal(this.state, nextState);
  },

  componentDidUpdate: function(nextProps, nextState) {
    if (nextState && this.state.id && this.isValidRule(nextState)) {
      this.updateRule(this.state);
    }
  },

  isValidRule: function(newState){
    var newState = newState || this.state;

    var hasVersion  = (newState.version && newState.versionMatch);
    var hasBuild = (newState.build && newState.buildMatch);
    var hasiOSVersion = (newState.iosVersion && newState.iosVersionMatch);
    if (!(hasVersion || hasBuild || hasiOSVersion)) {
      // not a valid override unless one of the overrides is selected.
      return false;
    }

    return LKConfigAPIClient.isValidValue(this.props.setting.kind, newState.value);
  },

  createRule: function() {
    this.setState({creating: true});

    var params = object.copy(this.state);
    params.bundleId = params['bundleId'];
    params.key = this.props.setting['key'];
    params.kind = this.props.setting['kind'];

    LKConfigAPIClient.createRule(params, {
      onSuccess: function(newRule) {
        // TODO(Lance): Separate "value" from "display value", probably during API parsing.
        if (newRule.value === false) {
          newRule.value = 'false';
        }

        this.setState(newRule);
        this.props.setIsPublished(false);
      },
      context: this
    });
  },

  updateRule: function(state) {
    if (this.timer) {
      clearTimeout(this.timer);
    }

    var rule = object.copy(state);
    this.timer = util.setTimeout(function() {
      LKConfigAPIClient.editRule(rule, {
        onSuccess: function(updatedRule) {
          this.props.setting['rules'][this.props.ruleIndex] = updatedRule;
          this.props.setUpdatedKey(this.props.setting, this.props.settingIndex);
          this.props.setIsPublished(false);
        },
        context: this
      });
    }, 500, this);
  },

  enableOverride: function(key) {
    var override = {};
    override[key] = (!this.state[key]) ? 1 : 0;
    this.setState(override);
  },

  render: function() {
    var setting = this.props.setting;
    return (
    <div className="expanded-light-box">
      <div className="row">
        <div className="col-xs-12">
          <label className="control-label">Default value is overridden to equal</label>
        </div>
      </div>

      <div className="row">
        <div className="col-xs-4 setting-rule-label">
          Value
        </div>
        <div className="col-xs-8">
          <div className="form-group">
          {(setting.kind == 'bool') ?
            <Select
              valueLink={this.linkState('value')}
              options={[
                {value:'', label:'Select a value'},
                {value:false, label:'False'},
                {value:true, label:'True'}
              ]} />
            :
            <input type="text" className="form-control" valueLink={this.linkState('value')}/>
          }
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-xs-12">
          <label className="control-label">When the following conditions are met</label>
        </div>
      </div>

      <div className="row">
        <div className="col-xs-4 setting-rule-label">
          Build
        </div>
        <div className="col-xs-4">
          <div className="form-group">
            <Select
              valueLink={this.linkState('buildMatch')}
              options={[
                {value:'', label:'anything'},
                {value:'gt', label:'greater than'},
                {value:'gte', label:'greater than or equal to'},
                {value:'eq', label:'equal to'},
                {value:'lte', label:'less than or equal to'},
                {value:'lt', label:'less than'}
              ]}
              onChange={(this.state.buildMatch == '') ? this.setState({build:''}) : null}/>
          </div>
        </div>
        <div className="col-xs-4 setting-rule-label">
          <input type="text" className="form-control" placeholder="build" disabled={!this.state.buildMatch} valueLink={this.linkState('build')}/>
        </div>
      </div>

      <div className="row">
        <div className="col-xs-4 setting-rule-label">
          App Version
        </div>
        <div className="col-xs-4">
          <div className="form-group">
            <Select
              valueLink={this.linkState('versionMatch')}
              options={[
                {value:'', label:'anything'},
                {value:'gt', label:'greater than'},
                {value:'gte', label:'greater than or equal to'},
                {value:'eq', label:'equal to'},
                {value:'lte', label:'less than or equal to'},
                {value:'lt', label:'less than'}
              ]}
              onChange={(this.state.versionMatch == '') ? this.setState({version:''}) : null}/>
          </div>
        </div>
        <div className="col-xs-4 setting-rule-label">
          <input type="text" className="form-control" placeholder="app version" disabled={!this.state.versionMatch} valueLink={this.linkState('version')}/>
        </div>
      </div>

      <div className="row">
        <div className="col-xs-4 setting-rule-label">
          iOS
        </div>
        <div className="col-xs-4">
          <div className="form-group">
            <Select
              valueLink={this.linkState('iosVersionMatch')}
              options={[
                {value:'', label:'anything'},
                {value:'gt', label:'greater than'},
                {value:'gte', label:'greater than or equal to'},
                {value:'eq', label:'equal to'},
                {value:'lte', label:'less than or equal to'},
                {value:'lt', label:'less than'}
              ]}
              onChange={(this.state.iosVersionMatch == '') ? this.setState({iosVersion:''}) : null}/>
          </div>
        </div>
        <div className="col-xs-4">
          <input type="text" className="form-control" placeholder="iOS version" disabled={!this.state.iosVersionMatch} valueLink={this.linkState('iosVersion')}/>
        </div>
      </div>

      {!this.state.id ?
        <div className="row">
          <div className="col-sm-8 col-sm-offset-4">
            <div className="form-group">

              {!this.isValidRule() ?
                <span>
                <button type="submit" className="btn btn-primary btn-sm" disabled>
                  Add Rule
                </button>
                <button type="submit" className="btn btn-link btn-sm" onClick={this.props.removeRule}>
                  Cancel
                </button>
                </span>
                :
                <button type="submit" className="btn btn-primary btn-sm" onClick={this.createRule} disabled={this.state.creating ? true : false}>
                  Add Rule
                </button>
              }
            </div>
          </div>
        </div>
        :
        <div className="row">
          <div className="col-sm-8 col-sm-offset-4">
            <div className="form-group">
              <button type="submit" className="btn btn-danger btn-xs" onClick={this.props.removeRule}>
                Delete
              </button>
            </div>
          </div>
        </div>
      }

    </div>
    )
  }
})

var SettingRules = React.createClass({
  getInitialState: function() {
    return {
      setting: this.props.setting
    }
  },

  addRule: function() {
    this.state.setting.rules.push({bundleId:this.props.setting.bundleId})
    this.setState({rules:this.state.rules})
  },

  removeRule: function(rule, i) {
    var params = this.state.setting.rules[i];
    if (params.id) {
      // rule is actually saved
      LKConfigAPIClient.deleteRule(params, {
        onSuccess: function() {
          // remove the rule from the ui
          var setting = update(this.state.setting, {rules: {$splice: [[i, 1]]}});
          this.setState({
            setting: setting
          });

          this.props.setUpdatedKey(setting, this.props.settingIndex);
          this.props.setIsPublished(false);
        },
        context: this
      })
    } else {
      var setting = update(this.state.setting, {rules: {$splice: [[i, 1]]}})
      this.setState({
        setting: setting
      })

      this.props.setUpdatedKey(setting, this.props.settingIndex);
    }
  },

  render: function() {
    return (
      <div className="panel panel-default">
        {this.props.setting.rules.map(function(rule,i){
          return <Rule
              setting={this.props.setting}
              removeRule={this.removeRule.bind(this, rule, i)}
              rule={rule}
              ruleIndex={i}
              key={rule.id}
              settingIndex={this.props.settingIndex}
              setIsPublished={this.props.setIsPublished}
              setUpdatedKey={this.props.setUpdatedKey} />
        }, this)}

        <div className="panel-heading">
          <a className="setting-add-override" onClick={this.addRule}>
            <i className="fa fa-plus"></i> Add new value override
          </a>
        </div>
      </div>
    )
  }
})

module.exports = SettingRules;