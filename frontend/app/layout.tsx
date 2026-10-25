import type { Metadata } from 'next';
import './globals.css';
import './aadin.css';
export const metadata: Metadata = {
  title: 'Company OS | سامانه جامع مدیریت سازمان',
  description: 'داشبورد فارسی مدیریت یکپارچه پروژه‌ها، وظایف، مالی، اسناد و منابع انسانی',
  icons: { icon: '/favicon.svg' },
};
export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="fa" dir="rtl" suppressHydrationWarning><body>{children}</body></html>;
}
