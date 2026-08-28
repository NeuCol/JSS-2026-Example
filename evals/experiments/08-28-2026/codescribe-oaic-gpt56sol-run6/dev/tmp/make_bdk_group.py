from pathlib import Path
import re

root=Path('software/mcfm/src/BDK')
files=['fvs','FFMPcc','FFPMccT','FFPMccTtilde','FFPMscT']

def logical(block):
    out=[]; cur=''
    for raw in block.splitlines():
        if not raw.strip() or raw[:1].lower() in ('c','!'): continue
        text=raw[6:].strip() if len(raw)>6 else ''
        if not text: continue
        cont=len(raw)>5 and raw[5] not in (' ','0')
        if cont: cur += ' '+text
        else:
            if cur: out.append(cur)
            cur=text
    if cur: out.append(cur)
    return out

def power(s):
    while '**' in s:
        p=s.index('**'); q=p-1
        if s[q]==')':
            depth=1; q-=1
            while q>=0:
                if s[q]==')': depth+=1
                elif s[q]=='(':
                    depth-=1
                    if depth==0:
                        while q>0 and (s[q-1].isalnum() or s[q-1]=='_'): q-=1
                        break
                q-=1
        else:
            while q>=0 and (s[q].isalnum() or s[q] in '._'): q-=1
            q+=1
        m=re.match(r'\*\*\s*([0-9]+)',s[p:]); n=m.group(1); end=p+m.end()
        s=s[:q]+'pow('+s[q:p]+','+n+')'+s[end:]
    return s

def expr(s):
    s=re.sub(r'([0-9.]+)_dp',r'\1',s,flags=re.I)
    s=re.sub(r'\bI3m\b','i3m',s,flags=re.I)
    s=re.sub(r'\bLnrat\b','lnrat',s,flags=re.I)
    s=re.sub(r'\bLsm1_2mht\b','Lsm1_2mht',s,flags=re.I)
    s=re.sub(r'\bLsm1_2mh\b','Lsm1_2mh',s,flags=re.I)
    s=re.sub(r'\bLsm1_2me\b','Lsm1_2me',s,flags=re.I)
    s=re.sub(r'\bLsm1\b','Lsm1',s,flags=re.I)
    s=re.sub(r'\bl0\b','L0',s,flags=re.I); s=re.sub(r'\bl1\b','L1',s,flags=re.I)
    return power(s)

def blocks(text):
    ls=text.splitlines(); starts=[i for i,x in enumerate(ls) if re.match(r'\s*function\s+',x,re.I)]
    return ['\n'.join(ls[a:(starts[k+1] if k+1<len(starts) else len(ls))]) for k,a in enumerate(starts)]

def assignments(block):
    return [x for x in logical(block) if '=' in x and not x.lower().startswith(('if','elseif'))]

def rhs_for(block,name):
    for x in assignments(block):
        if re.match(r'\s*'+re.escape(name)+r'\s*=',x,re.I): return expr(x.split('=',1)[1].strip())
    raise ValueError(name)

def lambda_line(stmt):
    left,right=stmt.split('=',1); m=re.match(r'(\w+)\((.*)\)',left.strip());
    args=', '.join('int '+x.strip() for x in m.group(2).split(','))
    return f'  const auto {m.group(1)} = [&](%s) {{ return %s; }};'%(args,expr(right.strip()))

def header(name):
    guard=name.upper()+'_HPP'
    return f'''#ifndef {guard}\n#define {guard}\n#include <FArray.hpp>\n#include <complex>\nstd::complex<double> {name}(int j1,int j2,int j3,int j4,int j5,int j6, FArray2D<std::complex<double>>& za, FArray2D<std::complex<double>>& zb);\n#endif\n'''

def wrapper(name):
    return f'''\nextern "C" std::complex<double> {name}_wrapper(int j1,int j2,int j3,int j4,int j5,int j6,std::complex<double>* za_data,std::complex<double>* zb_data) {{\n  FArray2D<std::complex<double>> za(za_data,14,14), zb(zb_data,14,14);\n  auto result={name}(j1,j2,j3,j4,j5,j6,za,zb);\n  result=result; // @coverage-probe\n  return result;\n}}\n'''

def shim(name):
    return f'''function {name}(j1,j2,j3,j4,j5,j6,za,zb) result(res)\n use, intrinsic :: iso_c_binding\n use types\n use mxpart_mod\n implicit none\n integer, intent(in) :: j1,j2,j3,j4,j5,j6\n complex(dp), intent(in), target :: za(mxpart,mxpart),zb(mxpart,mxpart)\n complex(dp) :: res\n interface\n  function wrap(j1,j2,j3,j4,j5,j6,za,zb) bind(C,name="{name}_wrapper") result(v)\n   import :: c_int,c_double_complex\n   integer(c_int),value :: j1,j2,j3,j4,j5,j6\n   complex(c_double_complex),intent(in) :: za(*),zb(*)\n   complex(c_double_complex) :: v\n  end function\n end interface\n res=wrap(j1,j2,j3,j4,j5,j6,za,zb)\nend function\n'''

simple={
'FFPMccT':['zab2','zab','zba'],
'FFPMccTtilde':['zab2','zab'],
'FFPMscT':['zab2','zab','zba','zb22b'],
}
for name,lams in simple.items():
    text=(root/(name+'.f')).read_text(); b=blocks(text)[0]; aa=assignments(b)
    lines=[f'#include "{name}.hpp"','#include <sprods_com_mod.hpp>','#include <W1jet.hpp>','#include <cmath>','using namespace sprods_com_mod;','',f'std::complex<double> {name}(int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb) {{']
    for lam in lams:
        st=next(x for x in aa if re.match(lam+r'\(',x,re.I)); lines.append(lambda_line(st))
    # scalar setup between lambdas and result
    for var in ['Delta3','delta12','delta34','delta56']:
        try: lines.append(f'  const double {var} = {rhs_for(b,var)};')
        except ValueError: pass
    lines += [f'  return {rhs_for(b,name)};','}',wrapper(name)]
    (root/(name+'.hpp')).write_text(header(name)); (root/(name+'.cpp')).write_text('\n'.join(lines)); (root/(name+'_fi.f90')).write_text(shim(name))

# fvs: three C++ functions, only Fvs public
text=(root/'fvs.f').read_text(); bs=blocks(text)
common=['#include "fvs.hpp"','#include <Need.hpp>','#include <sprods_com_mod.hpp>','#include <heldefs_mod.hpp>','#include <cmath>','using namespace sprods_com_mod;','using namespace heldefs_mod;','']
def body_func(b,name,lams):
    aa=assignments(b); out=[f'static std::complex<double> {name}(int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb) {{']
    for lam in lams: out.append(lambda_line(next(x for x in aa if re.match(lam+r'\(',x,re.I))))
    if name!='Fvs': out.append(f'  const double IDelta = {rhs_for(b,"IDelta")};')
    out += [f'  return {rhs_for(b,name)};','}','']
    return out
# helpers ordered before Fvs
lines=common+body_func(bs[2],'Brackpma',['t','delta','zab2'])+body_func(bs[1],'Brackpm',['t','delta','zab2'])
b=bs[0]; aa=assignments(b)
lines += ['std::complex<double> fvs_impl(int st,int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb) {',lambda_line(next(x for x in aa if re.match(r't\(',x,re.I))),lambda_line(next(x for x in aa if re.match(r'Brackppa\(',x,re.I))),lambda_line(next(x for x in aa if re.match(r'Brackpp\(',x,re.I))),'  if (st==hqpqbmgpgm) return Brackpm(j1,j2,j3,j4,j5,j6,za,zb)+Brackpm(j2,j1,j4,j3,j6,j5,zb,za);','  if (st==hqpqbmgpgp) return Brackpp(j1,j2,j3,j4,j5,j6)+Brackpp(j1,j2,j4,j3,j5,j6);','  return {};','}']
# exported lowercase C++ interface and wrapper
lines += ['std::complex<double> fvs(int st,int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb){ return fvs_impl(st,j1,j2,j3,j4,j5,j6,za,zb); }',wrapper('fvs')]
(root/'fvs.hpp').write_text(header('fvs')); (root/'fvs.cpp').write_text('\n'.join(lines)); (root/'fvs_fi.f90').write_text(shim('fvs'))

# FFMPcc with four functions
text=(root/'FFMPcc.f').read_text(); bs=blocks(text)
def ffbody(b,name,lams):
    aa=assignments(b); out=[f'static std::complex<double> {name}(int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb) {{']
    for lam in lams: out.append(lambda_line(next(x for x in aa if re.match(lam+r'\(',x,re.I))))
    if name=='FFMPcc_unsym': out.append(f'  const double delta12={rhs_for(b,"delta12")};')
    out += [f'  return {rhs_for(b,name)};','}','']; return out
lines=['#include "FFMPcc.hpp"','#include <Need.hpp>','#include <sprods_com_mod.hpp>','#include <W1jet.hpp>','#include <cmath>','using namespace sprods_com_mod;','']
lines+=ffbody(bs[2],'FFMPcc1',['zab2'])+ffbody(bs[3],'FFMPcc2',['zab2'])+ffbody(bs[1],'FFMPcc_unsym',['zab2','zba2','zab','za22a','zb21b','za21a'])
lines += ['std::complex<double> FFMPcc(int j1,int j2,int j3,int j4,int j5,int j6,FArray2D<std::complex<double>>& za,FArray2D<std::complex<double>>& zb) { return FFMPcc_unsym(j1,j2,j3,j4,j5,j6,za,zb)+FFMPcc_unsym(j2,j1,j4,j3,j6,j5,zb,za); }',wrapper('FFMPcc')]
(root/'FFMPcc.hpp').write_text(header('FFMPcc')); (root/'FFMPcc.cpp').write_text('\n'.join(lines)); (root/'FFMPcc_fi.f90').write_text(shim('FFMPcc'))

# move originals and wire CMake
(root/'deprecated').mkdir(exist_ok=True)
for name in files: (root/(name+'.f')).rename(root/'deprecated'/(name+'.f'))
p=root/'CMakeLists.txt'; cm=p.read_text()
for name in files: cm=cm.replace(name+'.f',name+'.cpp\n'+name+'_fi.f90')
p.write_text(cm)
