/** Display-only Persian integer to words; no accounting calculations. */
const persianNums=['','یک','دو','سه','چهار','پنج','شش','هفت','هشت','نه'];
const teens=['ده','یازده','دوازده','سیزده','چهارده','پانزده','شانزده','هفده','هجده','نوزده'];
const tens=['','','بیست','سی','چهل','پنجاه','شصت','هفتاد','هشتاد','نود'];
const hundreds=['','صد','دویست','سیصد','چهارصد','پانصد','ششصد','هفتصد','هشتصد','نهصد'];
function underThousand(n:number):string{const v:string[]=[];const h=Math.floor(n/100),r=n%100;if(h)v.push(hundreds[h]);if(r>=10&&r<20)v.push(teens[r-10]);else{const t=Math.floor(r/10);if(t)v.push(tens[t]);if(r%10)v.push(persianNums[r%10])}return v.join(' و ')}
/** Only safe integers, not decimals or financial calculation; number-to-words display utility. */
export function amountToPersianWords(value:number):string{if(!Number.isSafeInteger(value)||Math.abs(value)>999_999_999_999_999)throw Error('Number out of supported range');if(value===0)return 'صفر';const words:string[]=[];let n=Math.abs(value);const scales=['','هزار','میلیون','میلیارد','تریلیون'];let part=0;while(n){const r=n%1000;if(r){words.unshift([underThousand(r),scales[part]].filter(Boolean).join(' '))}n=Math.floor(n/1000);part++}return (value<0?'منفی ':'')+words.join(' و ')}
