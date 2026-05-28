/**
 * Custom G6 node: table-card
 * Renders a table card with header, field rows, type icons, and constraint labels.
 * Each field row has an anchor point on both left and right sides for field-level edges.
 */
import G6 from '@antv/g6'

const CARD_WIDTH = 210
const HEADER_H = 32
const ROW_H = 24
const PADDING = 8
const MAX_FIELDS = 8

G6.registerNode('table-card', {
  options: {
    size: [CARD_WIDTH, 120],
    style: { radius: 6, fill: '#fff', stroke: '#d9d9d9', lineWidth: 1 },
    stateStyles: {
      selected: { lineWidth: 3, stroke: '#1890FF', shadowColor: '#1890FF', shadowBlur: 10 },
      highlight: { shadowBlur: 8, shadowColor: '#52C41A', lineWidth: 2, stroke: '#52C41A' },
    },
  },

  draw(cfg, group) {
    const fields = cfg.fields || []
    const numFields = Math.min(fields.length, MAX_FIELDS)
    const totalH = HEADER_H + numFields * ROW_H + PADDING
    const w = CARD_WIDTH
    const hw = w / 2
    const hh = totalH / 2

    const stageColors = { CENTER: '#E6F7FF', UPSTREAM: '#F0F5FF', DOWNSTREAM: '#FFF7E6' }
    const stageBorders = { CENTER: '#1890FF', UPSTREAM: '#85A5FF', DOWNSTREAM: '#FFD591' }
    const headerColor = stageColors[cfg.stage] || '#F5F5F5'
    const borderColor = stageBorders[cfg.stage] || '#D9D9D9'
    const isCenter = cfg.stage === 'CENTER'

    // Main body (full rectangle with rounded corners)
    const keyShape = group.addShape('rect', {
      attrs: {
        x: -hw, y: -hh, width: w, height: totalH,
        radius: 6, fill: '#fff', stroke: borderColor,
        lineWidth: isCenter ? 3 : 1, cursor: 'pointer',
      },
      name: 'main-body', draggable: true,
    })

    // Header background (use a rect without radius to avoid G6 v4 array-radius issue)
    group.addShape('rect', {
      attrs: {
        x: -hw, y: -hh, width: w, height: HEADER_H,
        fill: headerColor,
      },
      name: 'header-bg', draggable: true,
    })

    // Table name
    group.addShape('text', {
      attrs: {
        x: -hw + 10, y: -hh + HEADER_H / 2,
        text: cfg.label || '未知表',
        textAlign: 'left', textBaseline: 'middle',
        fontWeight: 'bold', fontSize: 12, fill: '#333',
      },
      name: 'table-title', draggable: true,
    })

    // Stage badge
    if (isCenter) {
      group.addShape('rect', {
        attrs: {
          x: hw - 40, y: -hh + 6, width: 30, height: 18,
          radius: 3, fill: '#1890FF',
        },
        name: 'badge-bg',
      })
      group.addShape('text', {
        attrs: {
          x: hw - 25, y: -hh + 15,
          text: '当前', textAlign: 'center', textBaseline: 'middle',
          fontSize: 9, fill: '#fff', fontWeight: 'bold',
        },
        name: 'badge-text',
      })
    }

    // Field rows
    const shown = fields.slice(0, MAX_FIELDS)
    shown.forEach((field, i) => {
      const y = -hh + HEADER_H + i * ROW_H + ROW_H / 2
      const rowTop = -hh + HEADER_H + i * ROW_H

      // Type icon
      group.addShape('text', {
        attrs: {
          x: -hw + 8, y,
          text: typeIcon(field.type || ''),
          textAlign: 'center', textBaseline: 'middle',
          fontSize: 10, fill: '#888',
        },
        name: `field-${i}-icon`,
      })

      // Field name
      group.addShape('text', {
        attrs: {
          x: -hw + 22, y,
          text: field.name || '?',
          textAlign: 'left', textBaseline: 'middle',
          fontSize: 10, fill: '#333',
        },
        name: `field-${i}-name`,
      })

      // Constraint badges
      let cx = -hw + 22 + textWidth(field.name) + 6
      if (field.isPk) {
        cx = drawBadge(group, cx, y, 'PK', '#1890FF', `field-${i}-pk`)
      }
      if (field.isFk) {
        cx = drawBadge(group, cx, y, 'FK', '#FA8C16', `field-${i}-fk`)
      }
      // Operator type indicator for computed fields (AGGREGATE, CASE_WHEN, FUNCTION)
      if (field.mappingType && field.mappingType !== 'DIRECT') {
        cx = drawOpBadge(group, cx, y, field.mappingType, `field-${i}-op`)
      }

      // Invisible click target (on top of all field elements, last in group = highest z-order)
      group.addShape('rect', {
        attrs: {
          x: -hw, y: rowTop, width: w, height: ROW_H,
          fill: 'transparent', cursor: 'pointer',
        },
        name: `field-row-${i}`,
      })
    })

    // Expand hint
    if (fields.length > MAX_FIELDS) {
      const y = -hh + HEADER_H + MAX_FIELDS * ROW_H + ROW_H / 2
      group.addShape('text', {
        attrs: {
          x: 0, y,
          text: `全部 ${fields.length} 列 ∨`,
          textAlign: 'center', textBaseline: 'middle',
          fontSize: 9, fill: '#999', fontStyle: 'italic',
        },
        name: 'expand-hint',
      })
    }

    return keyShape
  },

  getAnchorPoints(cfg) {
    const fields = cfg.fields || []
    const numFields = Math.min(fields.length, MAX_FIELDS)
    const totalH = HEADER_H + numFields * ROW_H + PADDING
    const anchors = []

    // Left side anchors (0..N-1)
    for (let i = 0; i < numFields; i++) {
      anchors.push([0, (HEADER_H + i * ROW_H + ROW_H / 2) / totalH])
    }
    // Right side anchors (N..2N-1)
    for (let i = 0; i < numFields; i++) {
      anchors.push([1, (HEADER_H + i * ROW_H + ROW_H / 2) / totalH])
    }

    return anchors
  },

  setState(name, value, item) {
    const keyShape = item.getKeyShape()
    if (name === 'selected') {
      keyShape.attr('lineWidth', value ? 3 : 1)
      keyShape.attr('stroke', value ? '#1890FF' : '#d9d9d9')
      keyShape.attr('shadowBlur', value ? 10 : 0)
      keyShape.attr('shadowColor', value ? '#1890FF' : '')
    }
    if (name === 'highlight') {
      keyShape.attr('lineWidth', value ? 2 : 1)
      keyShape.attr('stroke', value ? '#52C41A' : '#d9d9d9')
      keyShape.attr('shadowBlur', value ? 8 : 0)
      keyShape.attr('shadowColor', value ? '#52C41A' : '')
    }
  },

  // Suppress default label drawing from single-node base — we draw labels in draw()
  drawLabel() {},
  afterDraw() {},
}, 'single-node')

function drawBadge(group, x, y, text, color, name) {
  group.addShape('rect', {
    attrs: {
      x, y: y - 7, width: 20, height: 14,
      radius: 2, fill: '#fff', stroke: color, lineWidth: 0.5,
    },
    name: `${name}-bg`,
  })
  group.addShape('text', {
    attrs: {
      x: x + 10, y,
      text, textAlign: 'center', textBaseline: 'middle',
      fontSize: 8, fill: color, fontWeight: 'bold',
    },
    name: `${name}-txt`,
  })
  return x + 24
}

function drawOpBadge(group, x, y, mappingType, name) {
  const symbols = { AGGREGATE: '∑', CASE_WHEN: '⇉', FUNCTION: 'ƒ' }
  const colors = { AGGREGATE: '#52C41A', CASE_WHEN: '#FA8C16', FUNCTION: '#722ED1' }
  const symbol = symbols[mappingType] || '⚙'
  const color = colors[mappingType] || '#888'
  group.addShape('text', {
    attrs: {
      x: x + 6, y,
      text: symbol,
      textAlign: 'center', textBaseline: 'middle',
      fontSize: 10, fill: color, fontWeight: 'bold',
    },
    name: `${name}-txt`,
  })
  return x + 14
}

function typeIcon(type) {
  const t = (type || '').toUpperCase()
  if (/INT|DECIMAL|DOUBLE|FLOAT|BIGINT|SMALLINT|TINYINT|NUMERIC/.test(t)) return '#'
  if (/VARCHAR|CHAR|STRING|TEXT/.test(t)) return 'Aa'
  if (/DATE|TIME|TIMESTAMP|DATETIME/.test(t)) return 'D'
  if (/BOOLEAN|BIT|BOOL/.test(t)) return '✓'
  return 'Aa'
}

/** Estimate pixel width of text at font-size 10px. CJK ≈ 14px, ASCII ≈ 7px. */
function textWidth(text) {
  if (!text) return 0
  let w = 0
  for (let i = 0; i < text.length; i++) {
    w += text.charCodeAt(i) > 127 ? 14 : 7
  }
  return w
}

export default G6
