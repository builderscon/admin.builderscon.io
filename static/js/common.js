  function fmtdate(dt) {
    var y = dt.getYear()+1900;
    var m = dt.getMonth()+1;
    var d = dt.getDate();
    return y + '-' +
      (m >= 10 ? m : '0' + m) + '-' +
      (d >= 10 ? d : '0' + d)
  }

  function fmttime(dt) {
    var h = dt.getHours();
    var m = dt.getMinutes();
    return (h >= 10 ? h : '0' + h) + ':' + (m >= 10 ? m : '0' + m);
  }
