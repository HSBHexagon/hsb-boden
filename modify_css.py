with open('src/styles/global.css', 'a') as f:
    f.write('''
.button-primary:focus-visible,
.button-secondary:focus-visible,
.button-secondary-dark:focus-visible {
  outline: 2px solid #cb0000;
  outline-offset: 2px;
}
''')
