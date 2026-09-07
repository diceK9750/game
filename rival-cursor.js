/* Adjacent-only serpentine walk; the final step reaches the actual CPU answer. */
(function () {
  'use strict';
  function rivalCursor(count, columns, target, progress) {
    if (!Number.isInteger(target) || target < 0 || target >= count || columns < 1) return null;
    const snake=[];
    for(let row=0;row<Math.ceil(count/columns);row++) {
      const cells=Array.from({length:Math.min(columns,count-row*columns)},(_,i)=>row*columns+i);
      snake.push(...(row%2?cells.reverse():cells));
    }
    if(count===1) return target;
    const cycle=[...snake,...snake.slice(1,-1).reverse()];
    const end=cycle.length+snake.indexOf(target);
    const steps=Math.min(8,cycle.length);
    const step=Math.min(steps,Math.floor(Math.max(0,Math.min(1,Number(progress)||0))*(steps+1)));
    return cycle[(end-steps+step)%cycle.length];
  }
  if(typeof module!=='undefined') module.exports={rivalCursor};
  if(typeof window!=='undefined') window.rivalCursor=rivalCursor;
})();
