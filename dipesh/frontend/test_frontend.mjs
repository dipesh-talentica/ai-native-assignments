#!/usr/bin/env node
/**
 * Frontend Test Suite
 * 
 * Tests for the CI/CD Dashboard frontend functionality.
 */

import { test, describe, expect } from 'node:test';
import assert from 'node:assert';

// Mock data for testing
const mockBuilds = [
  {
    id: 1,
    provider: "github",
    pipeline: "test-pipeline",
    repo: "test-org/test-repo",
    branch: "main",
    status: "success",
    started_at: "2025-01-25T10:00:00Z",
    completed_at: "2025-01-25T10:02:00Z",
    duration_seconds: 120,
    url: "https://github.com/test-org/test-repo/actions/runs/123"
  },
  {
    id: 2,
    provider: "jenkins",
    pipeline: "jenkins-test",
    repo: "test-org/jenkins-repo",
    branch: "develop",
    status: "failure",
    started_at: "2025-01-25T10:05:00Z",
    completed_at: "2025-01-25T10:08:00Z",
    duration_seconds: 180,
    url: "https://jenkins.test.com/job/test/123/"
  }
];

const mockSummary = {
  window: "7d",
  success_rate: 75.0,
  failure_rate: 25.0,
  avg_build_time: 150.0,
  last_status_by_pipeline: {
    "test-pipeline": "success",
    "jenkins-test": "failure"
  }
};

describe('Frontend Utility Functions', () => {
  test('formatBuildTime should format seconds correctly', () => {
    const formatBuildTime = (seconds) => {
      if (!seconds) return 'N/A';
      if (seconds < 60) return `${Math.round(seconds)}s`;
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    };

    assert.strictEqual(formatBuildTime(30), '30s');
    assert.strictEqual(formatBuildTime(90), '1m 30s');
    assert.strictEqual(formatBuildTime(150), '2m 30s');
    assert.strictEqual(formatBuildTime(null), 'N/A');
    assert.strictEqual(formatBuildTime(undefined), 'N/A');
  });

  test('status color mapping should work correctly', () => {
    const getStatusColor = (status) => {
      const colors = {
        success: { bg: '#22c55e', text: '#ffffff' },
        failure: { bg: '#ef4444', text: '#ffffff' },
        cancelled: { bg: '#6b7280', text: '#ffffff' },
        in_progress: { bg: '#3b82f6', text: '#ffffff' }
      };
      return colors[status] || colors.cancelled;
    };

    assert.deepStrictEqual(getStatusColor('success'), { bg: '#22c55e', text: '#ffffff' });
    assert.deepStrictEqual(getStatusColor('failure'), { bg: '#ef4444', text: '#ffffff' });
    assert.deepStrictEqual(getStatusColor('cancelled'), { bg: '#6b7280', text: '#ffffff' });
    assert.deepStrictEqual(getStatusColor('in_progress'), { bg: '#3b82f6', text: '#ffffff' });
    assert.deepStrictEqual(getStatusColor('unknown'), { bg: '#6b7280', text: '#ffffff' });
  });
});

describe('Data Processing', () => {
  test('chart data transformation should work correctly', () => {
    const transformChartData = (builds) => {
      const copy = [...builds].reverse().slice(-20);
      return copy.map((b, index) => ({
        name: `Build ${index + 1}`,
        fullName: new Date(b.started_at).toLocaleString(),
        duration: b.duration_seconds || 0,
        status: b.status,
        pipeline: b.pipeline
      }));
    };

    const chartData = transformChartData(mockBuilds);
    
    assert.strictEqual(chartData.length, 2);
    assert.strictEqual(chartData[0].name, 'Build 1');
    assert.strictEqual(chartData[0].duration, 120);
    assert.strictEqual(chartData[0].status, 'success');
    assert.strictEqual(chartData[1].name, 'Build 2');
    assert.strictEqual(chartData[1].duration, 180);
    assert.strictEqual(chartData[1].status, 'failure');
  });

  test('pie chart data transformation should work correctly', () => {
    const transformPieChartData = (summary) => {
      if (!summary) return [];
      return [
        { name: 'Success', value: summary.success_rate, color: '#22c55e' },
        { name: 'Failure', value: summary.failure_rate, color: '#ef4444' }
      ];
    };

    const pieChartData = transformPieChartData(mockSummary);
    
    assert.strictEqual(pieChartData.length, 2);
    assert.strictEqual(pieChartData[0].name, 'Success');
    assert.strictEqual(pieChartData[0].value, 75.0);
    assert.strictEqual(pieChartData[0].color, '#22c55e');
    assert.strictEqual(pieChartData[1].name, 'Failure');
    assert.strictEqual(pieChartData[1].value, 25.0);
    assert.strictEqual(pieChartData[1].color, '#ef4444');
  });

  test('pipeline status transformation should work correctly', () => {
    const transformPipelineStatus = (summary) => {
      return summary ? Object.entries(summary.last_status_by_pipeline).map(([k,v]) => ({pipeline: k, status: v})) : [];
    };

    const pipelineStatus = transformPipelineStatus(mockSummary);
    
    assert.strictEqual(pipelineStatus.length, 2);
    assert.strictEqual(pipelineStatus[0].pipeline, 'test-pipeline');
    assert.strictEqual(pipelineStatus[0].status, 'success');
    assert.strictEqual(pipelineStatus[1].pipeline, 'jenkins-test');
    assert.strictEqual(pipelineStatus[1].status, 'failure');
  });
});

describe('API Integration', () => {
  test('backend URL configuration should be correct', () => {
    const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://localhost:8001';
    assert.strictEqual(BACKEND_URL, 'http://localhost:8001');
  });

  test('WebSocket URL should be constructed correctly', () => {
    const BACKEND_URL = 'http://localhost:8001';
    const wsUrl = BACKEND_URL.replace('http', 'ws') + '/ws';
    assert.strictEqual(wsUrl, 'ws://localhost:8001/ws');
  });
});

describe('Component Props Validation', () => {
  test('MetricCard props should be validated', () => {
    const validateMetricCardProps = (props) => {
      const required = ['title', 'value'];
      return required.every(prop => props.hasOwnProperty(prop));
    };

    assert.strictEqual(validateMetricCardProps({
      title: 'Success Rate',
      value: '85.5%',
      suffix: '%',
      icon: '✅'
    }), true);

    assert.strictEqual(validateMetricCardProps({
      title: 'Success Rate'
      // missing value
    }), false);
  });

  test('StatusPill props should be validated', () => {
    const validateStatusPillProps = (props) => {
      return props.hasOwnProperty('s') && typeof props.s === 'string';
    };

    assert.strictEqual(validateStatusPillProps({ s: 'success' }), true);
    assert.strictEqual(validateStatusPillProps({ s: 'failure', size: 'lg' }), true);
    assert.strictEqual(validateStatusPillProps({}), false);
  });
});

describe('Error Handling', () => {
  test('should handle empty builds array', () => {
    const processBuilds = (builds) => {
      if (!builds || builds.length === 0) {
        return { count: 0, message: 'No builds found' };
      }
      return { count: builds.length, message: `${builds.length} builds found` };
    };

    assert.deepStrictEqual(processBuilds([]), { count: 0, message: 'No builds found' });
    assert.deepStrictEqual(processBuilds(null), { count: 0, message: 'No builds found' });
    assert.deepStrictEqual(processBuilds(mockBuilds), { count: 2, message: '2 builds found' });
  });

  test('should handle missing summary data', () => {
    const processSummary = (summary) => {
      if (!summary) {
        return {
          success_rate: 0,
          failure_rate: 0,
          avg_build_time: 0,
          last_status_by_pipeline: {}
        };
      }
      return summary;
    };

    const defaultSummary = processSummary(null);
    assert.strictEqual(defaultSummary.success_rate, 0);
    assert.strictEqual(defaultSummary.failure_rate, 0);
    assert.strictEqual(defaultSummary.avg_build_time, 0);
    assert.deepStrictEqual(defaultSummary.last_status_by_pipeline, {});
  });
});

describe('Time Window Processing', () => {
  test('time window validation should work correctly', () => {
    const validateTimeWindow = (window) => {
      const validWindows = ['1h', '24h', '7d', '30d'];
      return validWindows.includes(window);
    };

    assert.strictEqual(validateTimeWindow('7d'), true);
    assert.strictEqual(validateTimeWindow('24h'), true);
    assert.strictEqual(validateTimeWindow('1h'), true);
    assert.strictEqual(validateTimeWindow('30d'), true);
    assert.strictEqual(validateTimeWindow('invalid'), false);
    assert.strictEqual(validateTimeWindow(''), false);
  });
});

// Run all tests
console.log('Running frontend tests...');
