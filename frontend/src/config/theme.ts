import type { ThemeConfig } from 'antd'

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 4,
    fontSize: 14,
  },
  components: {
    Layout: {
      siderBg: '#001529',
      headerBg: '#fff',
      bodyBg: '#f0f2f5',
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#000c17',
      darkItemSelectedBg: '#1890ff',
    },
  },
}