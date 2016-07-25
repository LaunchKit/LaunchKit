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

var LKConfigAPIClient = library.api.LKConfigAPIClient;
var FormatCodeSample = library.react.config.codeformatting;
var shallowequal = library.react.lib.shallowequal;


var matches = {
  'gte' : '>=',
  'gt' : '>',
  'eq' : '==',
  'lte': '<=',
  'lt': '<'
};


var PreviewRules = React.createClass({

  render: function() {
    return (
      <span>
        {this.props.rules.map(function(rule){
          if (rule.kind == 'bool') {
            rule.value = String(rule.value);
          }
          return (
            <div className="rule-conditions">
              {(rule.kind == 'string') ?
                <span className={rule.kind}>"{rule.value}"</span>
                :
                <span className={rule.kind}>{rule.value}</span>
              },
              <div className="conditions">
                {(rule.build) ?
                  <span> when <span className="rule-condition">build {matches[rule.buildMatch]} <span className="int">{rule.build}</span></span></span>
                  :
                  null
                }
                {(rule.version) ?
                  <span>{(rule.build) ? ' and' : ' when'} <span className="rule-condition">app version {matches[rule.versionMatch]} <span className="int">{rule.version}</span></span></span>
                  :
                  null
                }
                {(rule.iosVersionMatch) ?
                  <span>{(rule.build || rule.version) ? ' and' : ' when'} <span className="rule-condition">iOS {matches[rule.iosVersionMatch]} <span className="int">{rule.iosVersion}</span></span></span>
                  :
                  null
                }
              </div>
            </div>
          )
        })}
      </span>
    )
  }

});

var ConfigPreview = React.createClass({
  getInitialState: function() {
    return {
      bundleId: 'id'
    }
  },

  render: function() {
    return (
      <dl className="setting-preview dl-horizontal">
        {this.props.settings.map(function(setting){
          if (setting.kind == 'bool') {
            setting.value = String(setting.value);
          }
          return [
            <dt className="settings-rule" key={setting.key}>
              <div className="settings-key">
                <FormatCodeSample setting={setting} />
              </div>
            </dt>,
            <dd>
              <div>
                {(setting.kind == 'string') ?
                  <span className={setting.kind}>"{setting.value}"</span>
                  :
                  <span className={setting.kind}>{setting.value}</span>
                }
              </div>
              <PreviewRules rules={setting.rules}/>
            </dd>
          ]
        })}
      </dl>
    )
  }
});

module.exports = ConfigPreview;